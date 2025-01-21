from dataclasses import dataclass
from typing import List, Optional
import difflib
from colorama import Fore, Style, init
import os

# Initialize colorama for cross-platform colored output
init()

@dataclass
class FileChange:
    """
    Represents a change between a template and its processed output.
    
    This class tracks both the original template content and the processed result,
    along with the file paths involved. This information is essential for both
    showing diffs and handling rollbacks if needed.
    
    Attributes:
        template_path: Path to the source template file
        output_path: Path where the processed file will be written
        original_content: The raw content of the template file
        processed_content: The content after variable substitution
    """
    template_path: str
    output_path: str
    original_content: str
    processed_content: str

class DiffFormatter:
    """
    Handles the formatting and display of differences between template and processed files.
    
    This class provides utilities for creating human-readable, colored diffs that
    clearly show what changes will be made during template processing. It uses
    the unified diff format for clarity and adds color coding for better visibility.
    """
    
    # Define color schemes for different types of diff lines
    COLORS = {
        'addition': Fore.GREEN,
        'deletion': Fore.RED,
        'header': Fore.CYAN,
        'separator': Style.DIM + Fore.WHITE
    }
    
    @classmethod
    def create_diff(cls, template_path: str, output_path: str, 
                   original: str, modified: str) -> str:
        """
        Creates a colored diff output showing template vs processed content.
        
        This method generates a unified diff between the original template content
        and the processed result, with color coding to highlight changes:
        - Red for removed lines
        - Green for added lines
        - Cyan for file headers
        - White for context
        
        Args:
            template_path: Path to the template file
            output_path: Path to the output file
            original: Original content from the template
            modified: Processed content to be written
            
        Returns:
            A formatted string containing the colored diff
        """
        # Generate unified diff
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile=f"Template: {cls._get_relative_path(template_path)}",
            tofile=f"Generated: {cls._get_relative_path(output_path)}",
            lineterm=""
        )
        
        # Format the diff with colors
        result = []
        for line in diff:
            if line.startswith('+'):
                if not line.startswith('+++'):
                    # Added line
                    result.append(f"{cls.COLORS['addition']}{line}{Style.RESET_ALL}")
                else:
                    # Header line
                    result.append(f"{cls.COLORS['header']}{line}{Style.RESET_ALL}")
            elif line.startswith('-'):
                if not line.startswith('---'):
                    # Removed line
                    result.append(f"{cls.COLORS['deletion']}{line}{Style.RESET_ALL}")
                else:
                    # Header line
                    result.append(f"{cls.COLORS['header']}{line}{Style.RESET_ALL}")
            else:
                # Context line
                result.append(line)
        
        return ''.join(result)
    
    @classmethod
    def show_changes(cls, changes: List[FileChange], 
                    context_lines: int = 3) -> None:
        """
        Displays all template processing changes with clear formatting.
        
        This method provides a comprehensive view of all changes that will be made,
        including file paths and formatted diffs. It's designed to give users
        a clear understanding of the impact of processing their templates.
        
        Args:
            changes: List of FileChange objects to display
            context_lines: Number of context lines to show around changes
        """
        if not changes:
            print(f"{Style.DIM}No changes detected.{Style.RESET_ALL}")
            return
        
        separator = cls.COLORS['separator'] + "=" * 80 + Style.RESET_ALL
        
        for i, change in enumerate(changes):
            # Print file information header
            print(f"\n{cls.COLORS['header']}Processing template file [{i+1}/{len(changes)}]:")
            print(f"  Source: {cls._get_relative_path(change.template_path)}")
            print(f"  Output: {cls._get_relative_path(change.output_path)}{Style.RESET_ALL}")
            
            # Print separator before diff
            print(separator)
            
            # Generate and print the diff
            diff = cls.create_diff(
                change.template_path,
                change.output_path,
                change.original_content,
                change.processed_content
            )
            print(diff)
            
            # Print separator after diff
            print(separator)
    
    @staticmethod
    def _get_relative_path(path: str) -> str:
        """
        Converts an absolute path to a relative path for cleaner display.
        
        This helper method makes the diff output more readable by showing
        relative paths instead of full system paths.
        
        Args:
            path: The full path to convert
            
        Returns:
            A relative path suitable for display
        """
        # Get the current working directory and the absolute path
        cwd = os.getcwd()
        abs_path = os.path.abspath(path)
        
        # Calculate relative path from current directory
        rel_path = os.path.relpath(abs_path, cwd)
        
        # Convert Windows backslashes to forward slashes for consistency
        return rel_path.replace(os.sep, '/')
        
    @classmethod
    def summarize_changes(cls, changes: List[FileChange]) -> str:
        """
        Creates a summary of all changes for logging or quick review.
        
        This method provides a high-level overview of what files will be
        affected by the template processing, without showing the full diffs.
        
        Args:
            changes: List of FileChange objects to summarize
            
        Returns:
            A formatted string summarizing all changes
        """
        if not changes:
            return "No changes to process."
        
        summary = [f"Found {len(changes)} template(s) to process:"]
        
        for change in changes:
            # Count lines added/removed
            old_lines = change.original_content.count('\n')
            new_lines = change.processed_content.count('\n')
            line_diff = new_lines - old_lines
            
            # Format the line difference
            if line_diff > 0:
                line_info = f"+{line_diff} lines"
            elif line_diff < 0:
                line_info = f"{line_diff} lines"
            else:
                line_info = "no line count change"
            
            # Add entry to summary
            summary.append(
                f"  • {cls._get_relative_path(change.template_path)} → "
                f"{cls._get_relative_path(change.output_path)} ({line_info})"
            )
        
        return "\n".join(summary)