"""
Database-backed authentication system for Gary-Zero.

This module provides secure authentication using PostgreSQL database with proper
password hashing, credential rotation, and security features.
"""

import secrets
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import check_password_hash, generate_password_hash

from framework.helpers import dotenv
from framework.helpers.print_style import PrintStyle


class DatabaseAuth:
    """Database-backed authentication system."""

    def __init__(self):
        """Initialize the database authentication system."""
        self.connection_string = self._get_database_url()
        self.print_style = PrintStyle()
        self._init_database()
        self._bootstrap_check()

    def _get_database_url(self) -> str:
        """Get PostgreSQL connection URL from environment."""
        # Try multiple environment variable names
        db_url = (
            dotenv.get_dotenv_value("DATABASE_URL")
            or dotenv.get_dotenv_value("POSTGRES_URL")
            or dotenv.get_dotenv_value("POSTGRES_PRISMA_URL")
        )

        if not db_url:
            raise RuntimeError(
                "No database URL found. Please set DATABASE_URL, POSTGRES_URL, or POSTGRES_PRISMA_URL environment variable."
            )

        return db_url

    def _get_connection(self):
        """Get a database connection."""
        try:
            conn = psycopg2.connect(
                self.connection_string, cursor_factory=RealDictCursor
            )
            return conn
        except Exception as e:
            self.print_style.error(f"Database connection failed: {e}")
            raise

    def _init_database(self):
        """Initialize the authentication database tables."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Create users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS auth_users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(512) NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        last_login TIMESTAMP NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        failed_login_attempts INTEGER DEFAULT 0,
                        locked_until TIMESTAMP NULL,
                        password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        must_change_password BOOLEAN DEFAULT FALSE
                    )
                """)

                # Create sessions table for session management
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS auth_sessions (
                        id SERIAL PRIMARY KEY,
                        session_token VARCHAR(512) UNIQUE NOT NULL,
                        user_id INTEGER REFERENCES auth_users(id) ON DELETE CASCADE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ip_address INET,
                        user_agent TEXT
                    )
                """)

                # Create OAuth tokens table (future-proofing)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS auth_oauth_tokens (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES auth_users(id) ON DELETE CASCADE,
                        provider VARCHAR(50) NOT NULL,
                        access_token TEXT NOT NULL,
                        refresh_token TEXT,
                        expires_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, provider)
                    )
                """)

                # Create indexes for performance
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_auth_users_username ON auth_users(username)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_auth_sessions_token ON auth_sessions(session_token)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires ON auth_sessions(expires_at)"
                )

                conn.commit()
                self.print_style.success(
                    "Authentication database initialized successfully"
                )

        except Exception as e:
            self.print_style.error(f"Failed to initialize authentication database: {e}")
            raise

    def _bootstrap_check(self):
        """Bootstrap check to ensure secure default credentials."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Check if any users exist
                cursor.execute("SELECT COUNT(*) FROM auth_users")
                user_count = cursor.fetchone()["count"]

                if user_count == 0:
                    # No users exist, create initial admin user
                    self._create_initial_admin()
                else:
                    # Check for insecure default credentials
                    self._check_insecure_defaults()

        except Exception as e:
            self.print_style.error(f"Bootstrap check failed: {e}")
            raise

    def _create_initial_admin(self):
        """Create initial admin user with secure credentials."""
        # Get credentials from environment or generate secure defaults
        username = dotenv.get_dotenv_value("AUTH_LOGIN", "admin")
        password = dotenv.get_dotenv_value("AUTH_PASSWORD")

        if not password:
            # Generate a secure random password
            password = secrets.token_urlsafe(32)
            self.print_style.warning(
                f"Generated secure password for user '{username}': {password}"
            )
            self.print_style.warning(
                "Please save this password and update your AUTH_PASSWORD environment variable!"
            )

            # Save to environment file for convenience
            try:
                dotenv.save_dotenv_value("AUTH_PASSWORD", password)
                self.print_style.success("Password saved to .env file")
            except Exception as e:
                self.print_style.error(f"Failed to save password to .env: {e}")

        # Abort if using insecure defaults
        if username == "admin" and password == "admin":
            raise RuntimeError(
                "SECURITY ERROR: Default insecure credentials detected (admin/admin). "
                "Please set secure AUTH_LOGIN and AUTH_PASSWORD environment variables."
            )

        # Create the initial admin user
        self.create_user(username, password, must_change_password=True)
        self.print_style.success(
            f"Initial admin user '{username}' created successfully"
        )

    def _check_insecure_defaults(self):
        """Check for and prevent insecure default credentials."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Check if admin user exists with potentially weak password
                cursor.execute(
                    "SELECT password_hash FROM auth_users WHERE username = %s",
                    ("admin",),
                )
                admin_user = cursor.fetchone()

                if admin_user:
                    # Check if it's using a weak password (admin/admin)
                    if check_password_hash(admin_user["password_hash"], "admin"):
                        raise RuntimeError(
                            "SECURITY ERROR: Admin user is using insecure default password 'admin'. "
                            "Please change the password immediately using the change_password method."
                        )

        except psycopg2.Error as e:
            self.print_style.error(f"Failed to check for insecure defaults: {e}")

    def create_user(
        self, username: str, password: str, must_change_password: bool = False
    ) -> bool:
        """Create a new user with hashed password.

        Args:
            username: Username for the new user
            password: Plain text password (will be hashed)
            must_change_password: Whether user must change password on first login

        Returns:
            True if user created successfully, False otherwise
        """
        try:
            password_hash = generate_password_hash(password)

            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO auth_users (username, password_hash, must_change_password, password_changed_at)
                    VALUES (%s, %s, %s, %s)
                """,
                    (username, password_hash, must_change_password, datetime.utcnow()),
                )

                conn.commit()
                self.print_style.success(f"User '{username}' created successfully")
                return True

        except psycopg2.IntegrityError:
            self.print_style.error(f"User '{username}' already exists")
            return False
        except Exception as e:
            self.print_style.error(f"Failed to create user '{username}': {e}")
            return False

    def authenticate_user(
        self, username: str, password: str, ip_address: str | None = None
    ) -> tuple[bool, dict | None]:
        """Authenticate a user with username and password.

        Args:
            username: Username to authenticate
            password: Plain text password
            ip_address: Client IP address for security logging

        Returns:
            Tuple of (success, user_data)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Get user data
                cursor.execute(
                    """
                    SELECT id, username, password_hash, is_active, failed_login_attempts,
                           locked_until, must_change_password, password_changed_at
                    FROM auth_users
                    WHERE username = %s
                """,
                    (username,),
                )

                user = cursor.fetchone()

                if not user:
                    self.print_style.warning(
                        f"Authentication failed: User '{username}' not found from {ip_address}"
                    )
                    return False, None

                # Check if account is locked
                if user["locked_until"] and user["locked_until"] > datetime.utcnow():
                    self.print_style.warning(
                        f"Authentication failed: Account '{username}' is locked until {user['locked_until']}"
                    )
                    return False, None

                # Check if account is active
                if not user["is_active"]:
                    self.print_style.warning(
                        f"Authentication failed: Account '{username}' is inactive"
                    )
                    return False, None

                # Verify password
                if not check_password_hash(user["password_hash"], password):
                    # Increment failed login attempts
                    failed_attempts = user["failed_login_attempts"] + 1
                    locked_until = None

                    # Lock account after 5 failed attempts for 15 minutes
                    if failed_attempts >= 5:
                        locked_until = datetime.utcnow() + timedelta(minutes=15)
                        self.print_style.warning(
                            f"Account '{username}' locked due to too many failed attempts"
                        )

                    cursor.execute(
                        """
                        UPDATE auth_users
                        SET failed_login_attempts = %s, locked_until = %s, updated_at = %s
                        WHERE id = %s
                    """,
                        (failed_attempts, locked_until, datetime.utcnow(), user["id"]),
                    )

                    conn.commit()

                    self.print_style.warning(
                        f"Authentication failed: Invalid password for '{username}' from {ip_address}"
                    )
                    return False, None

                # Authentication successful - reset failed attempts and update last login
                cursor.execute(
                    """
                    UPDATE auth_users
                    SET failed_login_attempts = 0, locked_until = NULL, last_login = %s, updated_at = %s
                    WHERE id = %s
                """,
                    (datetime.utcnow(), datetime.utcnow(), user["id"]),
                )

                conn.commit()

                user_data = dict(user)
                self.print_style.success(
                    f"User '{username}' authenticated successfully from {ip_address}"
                )
                return True, user_data

        except Exception as e:
            self.print_style.error(f"Authentication error for '{username}': {e}")
            return False, None

    def change_password(
        self, username: str, old_password: str, new_password: str
    ) -> bool:
        """Change user password with verification.

        Args:
            username: Username
            old_password: Current password for verification
            new_password: New password to set

        Returns:
            True if password changed successfully, False otherwise
        """
        try:
            # First authenticate with old password
            success, user_data = self.authenticate_user(username, old_password)

            if not success:
                self.print_style.error(
                    "Password change failed: Invalid current password"
                )
                return False

            # Generate new password hash
            new_password_hash = generate_password_hash(new_password)

            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE auth_users
                    SET password_hash = %s, password_changed_at = %s, must_change_password = FALSE, updated_at = %s
                    WHERE username = %s
                """,
                    (new_password_hash, datetime.utcnow(), datetime.utcnow(), username),
                )

                conn.commit()

                self.print_style.success(
                    f"Password changed successfully for user '{username}'"
                )
                return True

        except Exception as e:
            self.print_style.error(f"Failed to change password for '{username}': {e}")
            return False

    def rotate_credentials(self, username: str) -> str | None:
        """Rotate credentials by generating a new secure password.

        Args:
            username: Username to rotate credentials for

        Returns:
            New password if successful, None otherwise
        """
        try:
            # Generate new secure password
            new_password = secrets.token_urlsafe(32)
            new_password_hash = generate_password_hash(new_password)

            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE auth_users
                    SET password_hash = %s, password_changed_at = %s, must_change_password = TRUE, updated_at = %s
                    WHERE username = %s
                """,
                    (new_password_hash, datetime.utcnow(), datetime.utcnow(), username),
                )

                if cursor.rowcount == 0:
                    self.print_style.error(
                        f"User '{username}' not found for credential rotation"
                    )
                    return None

                conn.commit()

                self.print_style.success(f"Credentials rotated for user '{username}'")
                return new_password

        except Exception as e:
            self.print_style.error(
                f"Failed to rotate credentials for '{username}': {e}"
            )
            return None

    def create_session(
        self, user_id: int, ip_address: str | None = None, user_agent: str | None = None
    ) -> str | None:
        """Create a new session for authenticated user.

        Args:
            user_id: User ID
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Session token if successful, None otherwise
        """
        try:
            session_token = secrets.token_urlsafe(64)
            expires_at = datetime.utcnow() + timedelta(hours=24)  # 24 hour sessions

            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO auth_sessions (session_token, user_id, expires_at, ip_address, user_agent)
                    VALUES (%s, %s, %s, %s, %s)
                """,
                    (session_token, user_id, expires_at, ip_address, user_agent),
                )

                conn.commit()

                return session_token

        except Exception as e:
            self.print_style.error(f"Failed to create session: {e}")
            return None

    def validate_session(self, session_token: str) -> dict | None:
        """Validate a session token.

        Args:
            session_token: Session token to validate

        Returns:
            User data if session is valid, None otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT s.*, u.username, u.is_active
                    FROM auth_sessions s
                    JOIN auth_users u ON s.user_id = u.id
                    WHERE s.session_token = %s AND s.expires_at > %s AND u.is_active = TRUE
                """,
                    (session_token, datetime.utcnow()),
                )

                session = cursor.fetchone()

                if not session:
                    return None

                # Update last activity
                cursor.execute(
                    """
                    UPDATE auth_sessions
                    SET last_activity = %s
                    WHERE session_token = %s
                """,
                    (datetime.utcnow(), session_token),
                )

                conn.commit()

                return dict(session)

        except Exception as e:
            self.print_style.error(f"Session validation error: {e}")
            return None

    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    DELETE FROM auth_sessions
                    WHERE expires_at < %s
                """,
                    (datetime.utcnow(),),
                )

                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    self.print_style.debug(
                        f"Cleaned up {deleted_count} expired sessions"
                    )

        except Exception as e:
            self.print_style.error(f"Failed to cleanup expired sessions: {e}")

    def prepare_oauth_support(
        self,
        user_id: int,
        provider: str,
        access_token: str,
        refresh_token: str | None = None,
        expires_at: datetime | None = None,
    ) -> bool:
        """Store OAuth tokens for future OAuth implementation.

        Args:
            user_id: User ID
            provider: OAuth provider name (e.g., 'google', 'github')
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_at: Token expiration time

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO auth_oauth_tokens (user_id, provider, access_token, refresh_token, expires_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, provider)
                    DO UPDATE SET
                        access_token = EXCLUDED.access_token,
                        refresh_token = EXCLUDED.refresh_token,
                        expires_at = EXCLUDED.expires_at,
                        created_at = CURRENT_TIMESTAMP
                """,
                    (user_id, provider, access_token, refresh_token, expires_at),
                )

                conn.commit()

                self.print_style.success(
                    f"OAuth tokens stored for user {user_id} with provider {provider}"
                )
                return True

        except Exception as e:
            self.print_style.error(f"Failed to store OAuth tokens: {e}")
            return False
