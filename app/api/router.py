"""Aggregate API router — collects all sub-routers under /api/v1."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    health,
    jobs,
    kinetics,
    lookup,
    reactions,
    species,
    thermo,
    transition_states,
    uploads,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(lookup.router, prefix="/lookup", tags=["lookup"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(species.router, prefix="/species", tags=["species"])
api_router.include_router(
    species.entries_router, prefix="/species-entries", tags=["species-entries"]
)
api_router.include_router(reactions.router, prefix="/reactions", tags=["reactions"])
api_router.include_router(
    reactions.entries_router, prefix="/reaction-entries", tags=["reaction-entries"]
)
api_router.include_router(kinetics.router, prefix="/kinetics", tags=["kinetics"])
api_router.include_router(thermo.router, prefix="/thermo", tags=["thermo"])
api_router.include_router(
    transition_states.router,
    prefix="/transition-states",
    tags=["transition-states"],
)
