"""
Main entry point for the Panel Data Analysis App
"""
import subprocess
import sys


def main():
    """Launch the Gradio app"""
    print("Starting Panel Data Analysis App...")
    print("The app will open in your browser at http://127.0.0.1:7860")
    subprocess.run([sys.executable, "app.py"])


if __name__ == "__main__":
    main()
