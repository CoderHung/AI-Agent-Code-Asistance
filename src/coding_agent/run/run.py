#!/usr/bin/env python3

import os
import traceback
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

import typer
import yaml
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import PromptSession
from rich.console import Console

from coding_agent.agents.interactive import InteractiveAgent
from coding_agent.config import builtin_config_dir, get_config_path
from coding_agent.enviroment.local import LocalEnvironment
from coding_agent.models.litellm_model import LitellmModel
from coding_agent.run.extra.config import configure_if_first_time
from coding_agent.run.utils.save import save_traj
from coding_agent.utils.log import logger

DEFAULT_CONFIG = Path(os.getenv("CONFIG_PATH", builtin_config_dir / "agent.yaml"))
DEFAULT_OUTPUT = "last_run.traj.json"
console = Console(highlight=False)
app = typer.Typer(rich_markup_mode="rich")
prompt_session = PromptSession(history=FileHistory("task_history.txt"))
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
Console().print(
    f"Loading global config from [bold green]'{BASE_DIR}\\.env'[/bold green]"
)
load_dotenv(BASE_DIR / ".env")

# fmt: off
@app.command()
def main(
    model_name: str | None = typer.Option( None, "-m", "--model", help="Model to use",),
    task: str | None = typer.Option(None, "-t", "--task", help="Task/problem statement", show_default=False),
    yolo: bool = typer.Option(False, "-y", "--yolo", help="Run without confirmation"),
    cost_limit: float | None = typer.Option(None, "-l", "--cost-limit", help="Cost limit. Set to 0 to disable."),
    config_spec: Path = typer.Option(DEFAULT_CONFIG, "-c", "--config", help="Path to config file"),
    output: Path | None = typer.Option(DEFAULT_OUTPUT, "-o", "--output", help="Output trajectory file"),
    exit_immediately: bool = typer.Option( False, "--exit-immediately", help="Exit immediately when the agent wants to finish instead of prompting.", rich_help_panel="Advanced"),
) -> Any:
    # fmt: on
    configure_if_first_time()
    config_path = get_config_path(config_spec)
    console.print(f"Loading agent config from [bold green]'{config_path}'[/bold green]")
    config = yaml.safe_load(config_path.read_text())
    
    if not task:
        console.print("[bold yellow]What do you want to do?")
        task = prompt_session.prompt(
            "",
            multiline=True,
            bottom_toolbar=HTML(
                "Submit task: <b fg='yellow' bg='black'>Esc+Enter</b> | "
                "Navigate history: <b fg='yellow' bg='black'>Arrow Up/Down</b> | "
                "Search history: <b fg='yellow' bg='black'>Ctrl+R</b>"
            ),
        )
        console.print("[bold green]Got that, thanks![/bold green]")

    if yolo:
        config.setdefault("agent", {})["mode"] = "yolo"
    if cost_limit is not None:
        config.setdefault("agent", {})["cost_limit"] = cost_limit
    if exit_immediately:
        config.setdefault("agent", {})["confirm_exit"] = False
        
    model_config = config.get("model", {})
    if model_config is None:
        model_config = {}
        
    if model_name:
        model_config["model_name"] = model_name
    if from_env := os.getenv("MODEL_NAME"):
        model_config["model_name"] = from_env
    else:
        raise ValueError("No default model set.")

    if (from_env := os.getenv("MODEL_API_KEY")):
        model_config.setdefault("model_kwargs", {})["api_key"] = from_env
    model = LitellmModel(**model_config)
    
    env = LocalEnvironment(**config.get("env", {}))

    agent = InteractiveAgent(model, env, **config.get("agent", {}))
    exit_status, result, extra_info = None, None, None
    try:
        exit_status, result = agent.run(task)  # type: ignore[arg-type]
    except Exception as e:
        logger.error(f"Error running agent: {e}", exc_info=True)
        exit_status, result = type(e).__name__, str(e)
        extra_info = {"traceback": traceback.format_exc()}
    finally:
        if output:
            save_traj(agent, output, exit_status=exit_status, result=result, extra_info=extra_info)  # type: ignore[arg-type]
    return agent


if __name__ == "__main__":
    app()
