import argparse
import asyncio
import tornado
import subprocess


class MainHandler(tornado.web.RequestHandler):
    def initialize(self, index_file):
        self.index_file = index_file

    def get(self):
        # Load the HTML content with the button
        with open(self.index_file, "r") as f:
            html_content = f.read()
        self.write(html_content)


class ExecuteBashScriptHandler(tornado.web.RequestHandler):
    def initialize(self, exec_file):
        self.exec_file = exec_file

    def post(self):
        # Execute the Bash script
        try:
            self.write("Executing " + self.exec_file)
            print("Executing ", self.exec_file)
            subprocess.run([self.exec_file], check=True)
            self.set_status(200)
        except subprocess.CalledProcessError as e:
            self.set_status(500)
            self.write(f"Error executing Bash script: {e}")


def make_app(index_file, exec_file):
    return tornado.web.Application(
        [
            (r"/", MainHandler, {"index_file": index_file}),
            (r"/execute", ExecuteBashScriptHandler, {"exec_file": exec_file}),
        ]
    )


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index-file", default="index.html")
    parser.add_argument("--exec-file", default="update_mbudget.sh")
    args = parser.parse_args()
    index_file = args.index_file
    exec_file = args.exec_file
    app = make_app(index_file, exec_file)
    app.listen(8888)
    shutdown_event = asyncio.Event()
    await shutdown_event.wait()


if __name__ == "__main__":
    asyncio.run(main())
