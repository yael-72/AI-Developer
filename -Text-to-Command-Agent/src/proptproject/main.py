from proptproject.app import create_app


def main() -> None:
    demo = create_app()
    demo.launch()


if __name__ == "__main__":
    main()
