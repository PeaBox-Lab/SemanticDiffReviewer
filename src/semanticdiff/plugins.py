from __future__ import annotations

from importlib.metadata import entry_points
from typing import Any, Protocol


class SemanticDiffPlugin(Protocol):
    name:str
    def supports(self,left:Any,right:Any)->bool: ...
    def analyze(self,left:Any,right:Any)->dict[str,Any]: ...

def discover()->list[Any]:
    found=[]
    for ep in entry_points(group='semanticdiff.plugins'):
        try:
            found.append(ep.load()())
        except Exception as exc:  # noqa: BLE001
            # Plugin discovery must not abort other plugins.
            import logging
            logging.getLogger(__name__).warning("Failed to load plugin entry point %s: %s", ep, exc)
    return found

def run_plugins(left:Any,right:Any)->list[dict[str,Any]]:
    results=[]
    for plugin in discover():
        if plugin.supports(left,right): results.append({"plugin":plugin.name,"result":plugin.analyze(left,right)})
    return results
