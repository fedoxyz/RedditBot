import abc
import threading
import time
import sys
import select
import termios
import tty
from typing import List, Dict, Callable, Any, Optional

class Command:
    """
    Base class for commands in the terminal UI
    """
    def __init__(self, key: str, description: str):
        """
        Initialize a command
        
        :param key: Hotkey to trigger the command
        :param description: Description of the command
        """
        self.key = key
        self.description = description

    @abc.abstractmethod
    def execute(self, controller: 'TerminalController') -> Optional[str]:
        """
        Execute the command
        
        :param controller: The terminal controller instance
        :return: Optional status message
        """
        pass

class SystemCommand(Command):
    """
    Command for toggling system features
    """
    def __init__(self, 
                 key: str, 
                 description: str, 
                 toggle_method: Callable[[], str]):
        """
        Initialize a system command
        
        :param key: Hotkey to trigger the command
        :param description: Description of the command
        :param toggle_method: Method to toggle the system feature
        """
        super().__init__(key, description)
        self._toggle_method = toggle_method

    def execute(self, controller: 'TerminalController') -> str:
        """
        Execute the toggle method
        
        :param controller: The terminal controller instance
        :return: Status message from toggle method
        """
        return self._toggle_method()

class ViewCommand(Command):
    """
    Command for changing view
    """
    def __init__(self, 
                 key: str, 
                 description: str, 
                 view_name: str):
        """
        Initialize a view command
        
        :param key: Hotkey to trigger the command
        :param description: Description of the command
        :param view_name: Name of the view to switch to
        """
        super().__init__(key, description)
        self._view_name = view_name

    def execute(self, controller: 'TerminalController') -> Optional[str]:
        """
        Change the current view
        
        :param controller: The terminal controller instance
        :return: None
        """
        controller.current_view = self._view_name
        controller.page = 0
        return None

class PaginatedView:
    """
    Base class for paginated views
    """
    def __init__(self, items_per_page: int = 10):
        """
        Initialize a paginated view
        
        :param items_per_page: Number of items to display per page
        """
        self.items_per_page = items_per_page
        self.page = 0

    @abc.abstractmethod
    def get_items(self) -> List[Any]:
        """
        Retrieve items to be displayed
        
        :return: List of items
        """
        pass

    def get_paginated_items(self) -> tuple:
        """
        Get paginated items
        
        :return: Tuple of (current page items, total items)
        """
        items = self.get_items()
        start = self.page * self.items_per_page
        end = start + self.items_per_page
        return items[start:end], len(items)

    def next_page(self, total_items: int) -> bool:
        """
        Move to next page
        
        :param total_items: Total number of items
        :return: Whether page change was successful
        """
        max_page = (total_items + self.items_per_page - 1) // self.items_per_page - 1
        if self.page < max_page:
            self.page += 1
            return True
        return False

    def prev_page(self) -> bool:
        """
        Move to previous page
        
        :return: Whether page change was successful
        """
        if self.page > 0:
            self.page -= 1
            return True
        return False

class CommentView(PaginatedView):
    """
    Paginated view for comments
    """
    def __init__(self, comment_monitor, items_per_page: int = 10):
        """
        Initialize comment view
        
        :param comment_monitor: Comment monitor to retrieve comments from
        :param items_per_page: Number of comments per page
        """
        super().__init__(items_per_page)
        self.comment_monitor = comment_monitor

    def get_items(self) -> List[Any]:
        """
        Retrieve comments from monitor
        
        :return: List of comments
        """
        return self.comment_monitor.get_comments()

class TerminalController:
    """
    Advanced terminal-based control system
    """
    def __init__(self, 
                 voting_system, 
                 comment_monitor,
                 custom_views: Optional[Dict[str, PaginatedView]] = None):
        """
        Initialize terminal controller
        
        :param voting_system: The voting system to control
        :param comment_monitor: The comment monitor to control
        :param custom_views: Optional dictionary of custom views
        """
        # Systems
        self.voting_system = voting_system
        self.comment_monitor = comment_monitor
        
        # View management
        self.views = {
            'comments': CommentView(comment_monitor)
        }
        if custom_views:
            self.views.update(custom_views)
        
        # Command management
        self.commands: Dict[str, Dict[str, Command]] = {
            'main': {},
            'comments': {}
        }
        
        # Setup default commands
        self._setup_default_commands()
        
        # UI state
        self.current_view = 'main'
        self.running = True
        
        # Create lock for thread-safe operations
        self._lock = threading.Lock()

    def _setup_default_commands(self):
        """
        Setup default commands for main and comments views
        """
        # Main view commands
        main_commands = [
            SystemCommand('m', 'Toggle Monitoring', self.toggle_monitoring),
            SystemCommand('v', 'Toggle Voting', self.toggle_voting),
            ViewCommand('c', 'View Comments', 'comments'),
            Command('q', 'Quit Application', self.quit_application)
        ]
        
        # Comments view commands
        comments_commands = [
            Command('n', 'Next Page', self.next_page),
            Command('p', 'Previous Page', self.prev_page),
            ViewCommand('b', 'Back to Main Menu', 'main')
        ]
        
        # Register commands
        for cmd in main_commands:
            self.register_command('main', cmd)
        for cmd in comments_commands:
            self.register_command('comments', cmd)

    def register_command(self, view: str, command: Command):
        """
        Register a new command for a specific view
        
        :param view: View name to register command for
        :param command: Command to register
        """
        if view not in self.commands:
            self.commands[view] = {}
        self.commands[view][command.key] = command

    def register_view(self, name: str, view: PaginatedView):
        """
        Register a new view
        
        :param name: Name of the view
        :param view: View to register
        """
        self.views[name] = view

    def toggle_monitoring(self) -> str:
        """
        Toggle comment monitoring
        
        :return: Status message
        """
        with self._lock:
            if not self.comment_monitor.is_monitoring:
                self.comment_monitor.start_monitoring(self.comment_monitor.post_url)
                return "Monitoring Enabled"
            else:
                self.comment_monitor.stop_monitoring()
                return "Monitoring Disabled"

    def toggle_voting(self) -> str:
        """
        Toggle voting system
        
        :return: Status message
        """
        with self._lock:
            if not self.voting_system.running:
                self.voting_system.start()
                return "Voting Enabled"
            else:
                self.voting_system.stop()
                return "Voting Disabled"

    def next_page(self, _=None) -> Optional[str]:
        """
        Move to next page in current view
        
        :return: Optional status message
        """
        current_view = self.views.get(self.current_view)
        if isinstance(current_view, PaginatedView):
            items, total = current_view.get_paginated_items()
            if current_view.next_page(total):
                return "Moved to next page"
        return None

    def prev_page(self, _=None) -> Optional[str]:
        """
        Move to previous page in current view
        
        :return: Optional status message
        """
        current_view = self.views.get(self.current_view)
        if isinstance(current_view, PaginatedView):
            if current_view.prev_page():
                return "Moved to previous page"
        return None

    def quit_application(self, _=None) -> str:
        """
        Quit the application
        
        :return: Status message
        """
        self.running = False
        return "Shutting down..."

    def is_data(self) -> bool:
        """
        Check if there is input ready to be read
        
        :return: Whether input is available
        """
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

    def getch(self) -> Optional[str]:
        """
        Read a single character from terminal without blocking
        
        :return: Character read or None
        """
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1) if self.is_data() else None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def draw_view(self, status_message: str = ""):
        """
        Draw the current view
        
        :param status_message: Optional status message to display
        """
        print("\033c", end="")  # Clear screen
        
        if self.current_view == 'main':
            self._draw_main_menu(status_message)
        elif self.current_view in self.views:
            self._draw_paginated_view(status_message)

    def _draw_main_menu(self, status_message: str = ""):
        """
        Draw the main menu
        
        :param status_message: Optional status message to display
        """
        print("===== Reddit Bot Control Panel =====")
        print(f"Monitoring: {'Enabled' if self.comment_monitor.is_monitoring else 'Disabled'}")
        print(f"Voting:     {'Enabled' if self.voting_system.running else 'Disabled'}")
        print("\nHotkeys:")
        
        # Display commands for main view
        for cmd in sorted(self.commands['main'].values(), key=lambda x: x.key):
            print(f"{cmd.key} - {cmd.description}")

        if status_message:
            print(f"\nStatus: {status_message}")

    def _draw_paginated_view(self, status_message: str = ""):
        """
        Draw a paginated view
        
        :param status_message: Optional status message to display
        """
        current_view = self.views.get(self.current_view)
        if not current_view:
            return
        
        items, total_items = current_view.get_paginated_items()
        
        print(f"===== {self.current_view.capitalize()} View (Page {current_view.page + 1}) =====")
        print(f"Total Items: {total_items}")
        print("----------------------------------------")
        
        # Dynamic rendering based on view type
        if self.current_view == 'comments':
            for idx, comment in enumerate(items, 1):
                print(f"{idx}. Author: {comment.author}")
                print(f"   Score: {comment.score}")
                print(f"   Content: {comment.content[:100]}...")
                print("----------------------------------------")
        else:
            # Generic rendering for other views
            for idx, item in enumerate(items, 1):
                print(f"{idx}. {str(item)}")
                print("----------------------------------------")
        
        print("\nHotkeys:")
        for cmd in sorted(self.commands.get(self.current_view, {}).values(), key=lambda x: x.key):
            print(f"{cmd.key} - {cmd.description}")
        
        if status_message:
            print(f"\nStatus: {status_message}")

    def run(self):
        """
        Main control loop
        """
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            tty.setraw(fd)
            status_message = ""
            
            while self.running:
                # Draw current view
                self.draw_view(status_message)
                status_message = ""
                
                # Read key input
                key = self.getch()
                
                if not key:
                    time.sleep(0.1)
                    continue
                
                # Find and execute command for current view
                view_commands = self.commands.get(self.current_view, {})
                if key in view_commands:
                    try:
                        result = view_commands[key].execute(self)
                        if result:
                            status_message = result
                    except Exception as e:
                        status_message = f"Error: {str(e)}"
        
        finally:
            # Restore terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
        # Stop all systems when quitting
        self.voting_system.stop()
        self.comment_monitor.stop_monitoring()

def setup_control_system(voting_system, 
                         comment_monitor, 
                         custom_views: Optional[Dict[str, PaginatedView]] = None):
    """
    Setup and return a new terminal control system
    
    :param voting_system: The voting system to control
    :param comment_monitor: The comment monitor to control
    :param custom_views: Optional custom views to add
    :return: Configured TerminalController instance
    """
    return TerminalController(voting_system, comment_monitor, custom_views)

def run_control_system(control_system):
    """
    Run the control system in a separate thread
    
    :param control_system: The TerminalController instance to run
    :return: Control system thread
    """
    def control_thread_func():
        control_system.run()
    
    thread = threading.Thread(target=control_thread_func)
    thread.daemon = True
    thread.start()
    return thread
