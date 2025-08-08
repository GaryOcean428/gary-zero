# Claude Code CLI Usage

The Claude Code CLI tool provides access to Anthropic's Claude Code command‑line interface.  Only a subset of actions is currently supported.  To enable more actions, update `framework/tools/claude_code_cli.py` accordingly.

## Available Actions

{{available_actions}}

## Usage Examples

### Check CLI Status

```yaml
action: status
```

### Install the CLI (if auto‑install is enabled)

```yaml
action: install
```

Please specify one of the supported actions above.  Additional operations such as file editing and terminal commands will be added in future versions.