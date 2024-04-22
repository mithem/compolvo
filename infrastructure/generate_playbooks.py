import logging
import os

import click
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape


@click.command("generate")
@click.option("--config", "-c", default="playbooks.conf.yml", help="Path to playbooks config file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose mode")
def generate_playbooks(config: str, verbose: bool):
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    with open(config, "r") as stream:
        configuration = yaml.safe_load(stream)
    services = configuration["services"]
    version_counter = 0
    for service in services:
        name = service["system_name"]
        versions = service["versions"]
        for version in versions:
            env = Environment(loader=FileSystemLoader("ansible/templates"),
                              autoescape=select_autoescape())
            template = env.get_template(f"{name}.yml.jinja")
            content = template.render(version=version)
            service_dir = f"ansible/playbooks/{name}"
            if not os.path.isdir(service_dir):
                os.mkdir(service_dir)
            with open(f"ansible/playbooks/{name}/{version}.yml", "w") as stream:
                stream.write(content)
            logging.debug("Generated playbook for %s version %s", name, version)
            version_counter += 1
    logging.info("Generated %s playbooks across %s versions", len(services), version_counter)


if __name__ == "__main__":
    generate_playbooks()
