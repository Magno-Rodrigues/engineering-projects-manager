# init_modules.py

# This file initializes default modules for the application.

class Module:
    def __init__(self, name):
        self.name = name

class ProjectModule(Module):
    def __init__(self):
        super().__init__('projects')
        self.register()  # Register the Project module

    def register(self):
        print(f'{self.name} module has been registered.')


if __name__ == '__main__':
    # Initialize modules
    project_module = ProjectModule()