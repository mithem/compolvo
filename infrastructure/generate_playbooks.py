import logging
import os

import click
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape, Template


def write_to_template(template: Template, system_name: str, file_name: str, **kwargs):
    content = template.render(**kwargs)
    service_dir = f"ansible/playbooks/{system_name}"
    if not os.path.isdir(service_dir):
        os.makedirs(service_dir)
    with open(f"ansible/playbooks/{system_name}/{file_name}.yml", "w") as stream:
        stream.write(content)


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
        data = {"name": name}
        keys = ["apt_module", "brew_module", "winget_package", "pacman_package"]
        for key in keys:
            data[key] = service.get(key)
        template_file = service.get("template", f"{name}.yml.jinja")
        env = Environment(loader=FileSystemLoader("ansible/templates"),
                          autoescape=select_autoescape())
        template = env.get_template(template_file)
        for version in versions:
            logging.debug("Generated playbook for %s version %s", name, version)
            write_to_template(template, name, version, version=version, state="present", **data)
            version_counter += 1
        write_to_template(template, name, "uninstall", version=None, state="absent", **data)
    logging.info("Generated playbooks for %s service(s) across %s versions (%s files total)",
                 len(services), version_counter, version_counter + len(services))


@click.group()
def cli():
    pass


cli.add_command(generate_playbooks)

if __name__ == "__main__":
    cli()
