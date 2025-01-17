import os
import shutil
from typing import Dict, Optional
from datetime import datetime

class RollbackManager:
    """Manages backup and rollback of Kubernetes manifests"""
    
    def __init__(self):
        self.backup_dir: Optional[str] = None
        self.current_backup: Optional[Dict[str, str]] = None
    
    def backup_existing_manifests(self, directory: str) -> None:
        """
        Create backups of existing manifests before modification
        
        This creates both in-memory backups for quick rollback and
        on-disk backups for disaster recovery.
        """
        self.current_backup = {}
        
        # Create timestamped backup directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = os.path.join(
            directory,
            '.kustomize-backup',
            timestamp
        )
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Backup each manifest
        for root, _, files in os.walk(directory):
            # Skip .kustomize-backup directory
            if '.kustomize-backup' in root:
                continue
            
            for file in files:
                if file.endswith(('.yaml', '.yml')) and not file.startswith('.'):
                    file_path = os.path.join(root, file)
                    
                    # Create in-memory backup
                    with open(file_path, 'r') as f:
                        self.current_backup[file_path] = f.read()
                    
                    # Create on-disk backup
                    rel_path = os.path.relpath(file_path, directory)
                    backup_path = os.path.join(self.backup_dir, rel_path)
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(file_path, backup_path)
    
    def restore_manifests(self) -> None:
        """
        Restore manifests from backup after failed changes
        
        This uses the in-memory backup for quick restoration but
        preserves the on-disk backup for reference.
        """
        if not self.current_backup:
            print("Warning: No backup available for rollback")
            return
        
        print("\nRolling back changes...")
        
        for path, content in self.current_backup.items():
            try:
                with open(path, 'w') as f:
                    f.write(content)
                print(f"  ✓ Restored {path}")
            except Exception as e:
                print(f"  ✗ Failed to restore {path}: {str(e)}")
        
        print(f"\nBackup preserved in: {self.backup_dir}")
    
    def cleanup_old_backups(self, directory: str, keep_days: int = 7) -> None:
        """
        Clean up old backup directories
        
        Args:
            directory: Root directory containing .kustomize-backup
            keep_days: Number of days of backups to preserve
        """
        backup_root = os.path.join(directory, '.kustomize-backup')
        if not os.path.exists(backup_root):
            return
        
        cutoff = datetime.now().timestamp() - (keep_days * 86400)
        
        for backup_dir in os.listdir(backup_root):
            backup_path = os.path.join(backup_root, backup_dir)
            if os.path.getmtime(backup_path) < cutoff:
                try:
                    shutil.rmtree(backup_path)
                except Exception as e:
                    print(f"Warning: Failed to clean up {backup_path}: {str(e)}")
