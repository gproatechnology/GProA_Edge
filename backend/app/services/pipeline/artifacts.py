"""
Artifact persistence for intermediate processing results.
Enables replay, debugging, and incremental processing.
"""
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import pickle
import hashlib

logger = logging.getLogger(__name__)


class ArtifactStore:
    """Persist and retrieve intermediate pipeline artifacts."""
    
    ARTIFACT_NAMES = [
        "raw_parse.json",
        "entities.json",
        "relationships.json",
        "validation.json",
        "graph.pkl",
        "compliance.json",
        "identity_map.json",
        "reconciliation.json",
    ]
    
    def __init__(self, base_path: str = "artifacts"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _project_path(self, project_id: str, revision: str = "latest") -> Path:
        return self.base_path / project_id / revision
    
    def save(self, project_id: str, artifact_name: str, data: Any, revision: str = "latest"):
        """Save artifact to disk."""
        path = self._project_path(project_id, revision)
        path.mkdir(parents=True, exist_ok=True)
        
        file_path = path / artifact_name
        
        if file_path.suffix == ".json":
            with open(file_path, "w") as f:
                json.dump(data, f, default=str, indent=2)
        elif file_path.suffix == ".pkl":
            with open(file_path, "wb") as f:
                pickle.dump(data, f)
        else:
            with open(file_path, "w") as f:
                json.dump(data, f, default=str, indent=2)
        
        logger.info(f"Saved artifact: {project_id}/{revision}/{artifact_name}")
    
    def load(self, project_id: str, artifact_name: str, revision: str = "latest") -> Optional[Any]:
        """Load artifact from disk."""
        file_path = self._project_path(project_id, revision) / artifact_name
        
        if not file_path.exists():
            return None
        
        try:
            if file_path.suffix == ".pkl":
                with open(file_path, "rb") as f:
                    return pickle.load(f)
            else:
                with open(file_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load artifact {file_path}: {e}")
            return None
    
    def list_artifacts(self, project_id: str, revision: str = "latest") -> List[str]:
        """List all artifacts for a project revision."""
        path = self._project_path(project_id, revision)
        if not path.exists():
            return []
        return [f.name for f in path.iterdir() if f.is_file()]
    
    def create_revision(self, project_id: str, revision: str) -> Path:
        """Create a new revision directory."""
        path = self._project_path(project_id, revision)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_revision_hash(self, project_id: str, revision: str = "latest") -> str:
        """Generate hash of all artifacts for a revision."""
        path = self._project_path(project_id, revision)
        hasher = hashlib.md5()
        
        for artifact in sorted(self.list_artifacts(project_id, revision)):
            file_path = path / artifact
            with open(file_path, "rb") as f:
                hasher.update(f.read())
        
        return hasher.hexdigest()


artifact_store = ArtifactStore()