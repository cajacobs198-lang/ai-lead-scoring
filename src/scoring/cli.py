import json
import click
from pathlib import Path
from .rules import load_rules
from .score import score_lead


@click.group()
def cli():
    pass


@cli.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True))
@click.option("--rules", "rules_path", required=True, type=click.Path(exists=True))
@click.option("--no-llm", is_flag=True, help="Skip LLM signals even if enabled in YAML")
def score(input_path: str, rules_path: str, no_llm: bool):
    """Score one or more leads from a JSON file (single object or array)."""
    rs = load_rules(rules_path)
    if no_llm:
        rs.llm_enabled = False
    raw = json.loads(Path(input_path).read_text())
    leads = raw if isinstance(raw, list) else [raw]
    for lead in leads:
        click.echo(json.dumps(score_lead(lead, rs), indent=2))


if __name__ == "__main__":
    cli()
