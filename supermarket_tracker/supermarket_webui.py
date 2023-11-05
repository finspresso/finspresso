import asyncio
import tornado
import subprocess


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        # Load the HTML content with the button
        with open("index_supermarket.html", "r") as f:
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


def make_app():
    return tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/execute", ExecuteBashScriptHandler),
        ]
    )


async def main():
    app = make_app()
    app.listen(8888)
    shutdown_event = asyncio.Event()
    await shutdown_event.wait()


if __name__ == "__main__":
    asyncio.run(main())
