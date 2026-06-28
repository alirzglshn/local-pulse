from django.apps import AppConfig

class CoreConfig((AppConfig)):
    name = "core"
    

    # making the index run onc at startup
    def ready(self):
        from . indexes import create_indexes
        create_indexes