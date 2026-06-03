import os
import urllib.request
import ssl
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Downloads external JS libraries (Vue, Plotly) for local usage using standard libraries'

    def handle(self, *args, **kwargs):
        # Define target directory
        static_dir = settings.BASE_DIR / 'static' / 'js' / 'vendor'
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
            self.stdout.write(f"Created directory: {static_dir}")

        # Define libraries to download
        libs = [
            {
                'name': 'vue.global.js',
                'url': 'https://unpkg.com/vue@3/dist/vue.global.js'
            },
            {
                'name': 'plotly.min.js',
                'url': 'https://cdn.plot.ly/plotly-2.27.0.min.js'
            }
        ]

        # Bypass SSL verification if needed (sometimes helps with local dev envs)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        for lib in libs:
            self.stdout.write(f"Downloading {lib['name']}...")
            try:
                # Use standard library urllib
                with urllib.request.urlopen(lib['url'], context=ctx) as response:
                    data = response.read()
                    file_path = static_dir / lib['name']
                    with open(file_path, 'wb') as f:
                        f.write(data)
                    self.stdout.write(self.style.SUCCESS(f"Saved to {file_path}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error downloading {lib['name']}: {e}"))

        self.stdout.write(self.style.SUCCESS("All libraries downloaded successfully!"))
