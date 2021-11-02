import sys


def web_app(voila_app, env):
    try:
        from fps_uvicorn.cli import app as fps_app
        from fps_voila.routes import init_fps
    except Exception:
        print("Please install fps_voila.")
        sys.exit(1)

    # pass options to FPS app
    sys.argv = sys.argv[:1]
    fps_options = [f"--fps_uvicorn.root_path={voila_app.server_url}", f"--port={voila_app.port}", "--authenticator.mode=noauth"]
    sys.argv += fps_options
    init_fps(
        notebook_path=voila_app.notebook_path,
        template_paths=voila_app.template_paths,
        config=voila_app.config,
        voila_configuration=voila_app.voila_configuration,
        contents_manager=voila_app.contents_manager,
        base_url=voila_app.base_url,
        kernel_manager=voila_app.kernel_manager,
        kernel_spec_manager=voila_app.kernel_spec_manager,
        allow_remote_access=True,
        autoreload=voila_app.autoreload,
        voila_jinja2_env=env,
        jinja2_env=env,
        static_path='/',
        server_root_dir='/',
        config_manager=voila_app.config_manager,
        static_paths=voila_app.static_paths,
        settings=voila_app.tornado_settings,
        log=voila_app.log,
        whitelist=voila_app.voila_configuration.file_whitelist,
        blacklist=voila_app.voila_configuration.file_blacklist,
        root_dir=voila_app.root_dir,
    )
    fps_app()
