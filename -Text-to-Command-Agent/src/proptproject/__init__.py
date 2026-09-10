from proptproject.app import create_app


def main() -> None:
    demo = create_app()
    demo.launch()

