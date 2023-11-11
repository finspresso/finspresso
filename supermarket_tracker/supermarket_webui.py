import argparse
import asyncio
import tornado
import subprocess


class MainHandler(tornado.web.RequestHandler):
    def __init__(self, index_file):
        super().__init__()
        self.index_file = index_file

    def get(self):
        # Load the HTML content with the button
        with open(self.index_file, "r") as f:
            html_content = f.read()
        self.write(html_content)


class ExecuteBashScriptHandler(tornado.web.RequestHandler):
    def post(self):
        # Execute the Bash script
        try:
            self.write("Executing my script (POST)")
            print("Executing my script (POST)")
            subprocess.run(["mytest.sh"], check=True)
            self.set_status(200)
        except subprocess.CalledProcessError as e:
            self.set_status(500)
            self.write(f"Error executing Bash script: {e}")


def make_app(index_file):
    return tornado.web.Application(
        [
            (r"/", MainHandler(index_file=index_file)),
            (r"/execute", ExecuteBashScriptHandler),
        ]
    )


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index-file", default="index_supermarket.html")
    args = parser.parse_args()
    index_file = args.index_file
    app = make_app(index_file)
    app.listen(8888)
    shutdown_event = asyncio.Event()
    await shutdown_event.wait()


if __name__ == "__main__":
    asyncio.run(main())
