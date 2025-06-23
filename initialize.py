import asyncio

import models
from agent import AgentConfig, ModelConfig
from zero.helpers import runtime, settings
from zero.helpers.defer import DeferredTask


def initialize_agent():
    current_settings = settings.get_settings()

    # chat model from user settings
    chat_llm = ModelConfig(
        provider=models.ModelProvider[current_settings["chat_model_provider"]],
        name=current_settings["chat_model_name"],
        ctx_length=current_settings["chat_model_ctx_length"],
        vision=current_settings["chat_model_vision"],
        limit_requests=current_settings["chat_model_rl_requests"],
        limit_input=current_settings["chat_model_rl_input"],
        limit_output=current_settings["chat_model_rl_output"],
        kwargs=current_settings["chat_model_kwargs"],
    )

    # utility model from user settings
    utility_llm = ModelConfig(
        provider=models.ModelProvider[current_settings["util_model_provider"]],
        name=current_settings["util_model_name"],
        ctx_length=current_settings["util_model_ctx_length"],
        limit_requests=current_settings["util_model_rl_requests"],
        limit_input=current_settings["util_model_rl_input"],
        limit_output=current_settings["util_model_rl_output"],
        kwargs=current_settings["util_model_kwargs"],
    )
    # embedding model from user settings
    embedding_llm = ModelConfig(
        provider=models.ModelProvider[current_settings["embed_model_provider"]],
        name=current_settings["embed_model_name"],
        limit_requests=current_settings["embed_model_rl_requests"],
        kwargs=current_settings["embed_model_kwargs"],
    )
    # browser model from user settings
    browser_llm = ModelConfig(
        provider=models.ModelProvider[current_settings["browser_model_provider"]],
        name=current_settings["browser_model_name"],
        vision=current_settings["browser_model_vision"],
        kwargs=current_settings["browser_model_kwargs"],
    )
    # agent configuration
    config = AgentConfig(
        chat_model=chat_llm,
        utility_model=utility_llm,
        embeddings_model=embedding_llm,
        browser_model=browser_llm,
        mcp_servers=current_settings["mcp_servers"],
    )

    # update SSH and docker settings
    _set_runtime_config(config, current_settings)

    # update config with runtime args
    _args_override(config)

    # initialize MCP in deferred task to prevent blocking the main thread
    import agent as agent_helper
    import zero.helpers.mcp_handler as mcp_helper
    import zero.helpers.print_style as print_style_helper

    if not mcp_helper.MCPConfig.get_instance().is_initialized():
        try:
            mcp_helper.MCPConfig.update(config.mcp_servers)
        except Exception as e:
            first_context = agent_helper.AgentContext.first()
            if first_context:
                first_context.log.log(
                    type="warning",
                    content=f"Failed to update MCP settings: {e}",
                    temp=False,
                )
                print_style_helper.PrintStyle(
                    background_color="black", font_color="red", padding=True
                ).print(f"Failed to update MCP settings: {e}")

    # return config object
    return config


def initialize_mcp() -> DeferredTask:
    """Initializes MCP servers in a deferred task."""
    from zero.helpers.mcp_handler import initialize_mcp as mcp_init_servers

    async def deferred_initialize_mcp_async():
        current_settings = settings.get_settings()
        mcp_servers_config = current_settings.get("mcp_servers")
        if mcp_servers_config:
            # Run the synchronous mcp_init_servers in a separate thread to avoid blocking
            await asyncio.to_thread(mcp_init_servers, mcp_servers_config)

    return DeferredTask().start_task(deferred_initialize_mcp_async)


def initialize_chats() -> DeferredTask:
    from zero.helpers import persist_chat

    async def initialize_chats_async():
        persist_chat.load_tmp_chats()

    return DeferredTask().start_task(initialize_chats_async)


def initialize_job_loop() -> DeferredTask:
    from zero.helpers.job_loop import run_loop

    return DeferredTask("JobLoop").start_task(run_loop)


def _args_override(config):
    # update config with runtime args
    for key, value in runtime.args.items():
        if hasattr(config, key):
            # conversion based on type of config[key]
            if isinstance(getattr(config, key), bool):
                value = value.lower().strip() == "true"
            elif isinstance(getattr(config, key), int):
                value = int(value)
            elif isinstance(getattr(config, key), float):
                value = float(value)
            elif isinstance(getattr(config, key), str):
                value = str(value)
            else:
                raise Exception(
                    f"Unsupported argument type of '{key}': " f"{type(getattr(config, key))}"
                )

            setattr(config, key, value)


def _set_runtime_config(config: AgentConfig, set: settings.Settings):
    ssh_conf = settings.get_runtime_config(set)
    for key, value in ssh_conf.items():
        if hasattr(config, key):
            setattr(config, key, value)

    # if config.code_exec_docker_enabled:
    #     config.code_exec_docker_ports["22/tcp"] = ssh_conf["code_exec_ssh_port"]
    #     config.code_exec_docker_ports["80/tcp"] = ssh_conf["code_exec_http_port"]
    #     config.code_exec_docker_name = f"{config.code_exec_docker_name}-{ssh_conf['code_exec_ssh_port']}-{ssh_conf['code_exec_http_port']}"

    #     dman = docker.DockerContainerManager(
    #         logger=log.Log(),
    #         name=config.code_exec_docker_name,
    #         image=config.code_exec_docker_image,
    #         ports=config.code_exec_docker_ports,
    #         volumes=config.code_exec_docker_volumes,
    #     )
    #     dman.start_container()

    # config.code_exec_ssh_pass = asyncio.run(rfc_exchange.get_root_password())
