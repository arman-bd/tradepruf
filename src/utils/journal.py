from datetime import datetime
from pathlib import Path
from typing import Optional, Union, TextIO
import sys

class JournalWriter:
    """Handles writing journal entries to file and optionally to stdout."""
    
    def __init__(
        self,
        filename: Optional[Union[str, Path]] = None,
        directory: str = "journals",
        stdout: bool = True,
        mode: str = "w"
    ):
        """Initialize journal writer.
        
        Args:
            filename: Specific filename to use. If None, generates timestamp-based name
            directory: Directory to store journal files
            stdout: Whether to also print to standard output
            mode: File open mode ('w' for write, 'a' for append)
        """
        self.stdout = stdout
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=True)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"journal_{timestamp}.txt"
        
        self.filepath = self.directory / filename
        self.file: Optional[TextIO] = None
        self.mode = mode
        
    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        
    def open(self):
        """Open the journal file."""
        if self.file is None:
            self.file = open(self.filepath, self.mode, encoding='utf-8')
            
    def close(self):
        """Close the journal file."""
        if self.file is not None:
            self.file.close()
            self.file = None
            
    def write(self, message: str, timestamp: bool = False, printable: bool = None):
        """Write a message to the journal.
        
        Args:
            message: Message to write
            timestamp: Whether to include timestamp
            printable: Override default stdout setting
        """
        try:
            if self.file is None:
                self.open()
                
            # Add timestamp if requested
            if timestamp:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                entry = f"[{current_time}] {message}"
            else:
                entry = message
                
            # Write to file
            self.file.write(entry + "\n")
            self.file.flush()  # Ensure immediate write
            
            # Print to stdout if enabled
            should_print = self.stdout if printable is None else printable
            if should_print:
                print(entry)
                
        except Exception as e:
            print(f"Error writing to journal: {str(e)}", file=sys.stderr)
            
    def section(self, title: str, printable: bool = None):
        """Write a section header to the journal."""
        separator = "=" * 80
        self.write(separator, timestamp=False, printable=printable)
        self.write(f"=== {title} ===", timestamp=False, printable=printable)
        self.write(separator, timestamp=False, printable=printable)
        
    def subsection(self, title: str, printable: bool = None):
        """Write a subsection header to the journal."""
        separator = "-" * 60
        self.write(separator, timestamp=False, printable=printable)
        self.write(f"--- {title} ---", timestamp=True, printable=printable)
        self.write(separator, timestamp=False, printable=printable)
        
    def trade(
        self,
        action: str,
        symbol: str,
        shares: float,
        price: float,
        total: float,
        printable: bool = None
    ):
        """Write a trade entry to the journal."""
        message = (
            f"TRADE: {action} {shares:.3f} {symbol} @ ${price:.2f} "
            f"(Total: ${total:.2f})"
        )
        self.write(message, printable=printable)
        
    def metric(self, name: str, value: Union[str, int, float], printable: bool = None):
        """Write a metric entry to the journal."""
        if isinstance(value, float):
            message = f"{name}: {value:.2f}"
        else:
            message = f"{name}: {value}"
        self.write(message, printable=printable)