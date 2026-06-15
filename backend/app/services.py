from __future__ import annotations

from typing import Any

from backend.app.config import Settings
from backend.app.waha_client import WahaClient, WahaError


def normalize_group_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


def find_groups_by_name(groups: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    query = normalize_group_name(name)
    if not query:
        return []

    exact = [
        g
        for g in groups
        if normalize_group_name(str(g.get("subject") or g.get("name") or "")) == query
    ]
    if exact:
        return exact

    return [
        g
        for g in groups
        if query in normalize_group_name(str(g.get("subject") or g.get("name") or ""))
    ]


def group_display_name(group: dict[str, Any]) -> str:
    return str(group.get("subject") or group.get("name") or group.get("id") or "Unknown")


def group_id(group: dict[str, Any]) -> str:
    gid = group.get("id") or group.get("groupId") or group.get("jid")
    if not gid:
        raise WahaError("Group has no id field", detail=group)
    return str(gid)


def extract_participant_ids(participants: list[dict[str, Any]], *, exclude_ids: set[str] | None = None) -> list[str]:
    exclude = {x.lower() for x in (exclude_ids or set())}
    ids: list[str] = []
    seen: set[str] = set()

    for p in participants:
        role = str(p.get("role") or "").lower()
        if role == "left":
            continue
        pid = p.get("id") or p.get("jid")
        if not pid:
            continue
        pid_str = str(pid)
        key = pid_str.lower()
        if key in exclude or key in seen:
            continue
        seen.add(key)
        ids.append(pid_str)

    return ids


async def copy_group_members(
    client: WahaClient,
    settings: Settings,
    *,
    source_group_name: str,
    new_group_name: str,
    source_group_id: str | None = None,
) -> dict[str, Any]:
    new_name = new_group_name.strip()
    if not new_name:
        raise WahaError("New group name is required")

    groups = await client.list_groups()
    if source_group_id:
        source = next((g for g in groups if group_id(g) == source_group_id), None)
        if not source:
            raise WahaError(f"Source group id not found: {source_group_id}")
    else:
        matches = find_groups_by_name(groups, source_group_name)
        if not matches:
            raise WahaError(
                f'No group found matching "{source_group_name}". '
                "Check the name or pick from the group list."
            )
        if len(matches) > 1:
            return {
                "status": "ambiguous",
                "message": "Multiple groups match this name. Pick one from the list.",
                "matches": [
                    {"id": group_id(g), "name": group_display_name(g), "size": g.get("size")}
                    for g in matches
                ],
            }
        source = matches[0]

    src_id = group_id(source)
    participants = await client.get_participants(src_id)

    me = await client.get_session_me()
    my_ids = {
        str(me.get("id") or ""),
        str(me.get("lid") or ""),
    }
    my_ids = {x.lower() for x in my_ids if x}

    member_ids = extract_participant_ids(participants, exclude_ids=my_ids)
    if not member_ids:
        raise WahaError("No members to copy (group may be empty or only you are listed).")

    batch_size = settings.participant_batch_size
    initial = member_ids[:batch_size]
    remaining = member_ids[batch_size:]

    created = await client.create_group(
        new_name,
        [{"id": pid} for pid in initial],
    )

    new_group = created if isinstance(created, dict) else {}
    new_id = (
        new_group.get("id")
        or new_group.get("groupId")
        or new_group.get("jid")
        or (new_group.get("group") or {}).get("id")
    )
    if not new_id:
        raise WahaError("Group created but WAHA did not return group id", detail=created)

    add_results: list[dict[str, Any]] = []
    if remaining:
        add_results = await client.add_participants_batched(
            str(new_id),
            remaining,
            batch_size=batch_size,
            delay_ms=settings.participant_batch_delay_ms,
        )

    failed_batches = [r for r in add_results if not r.get("ok")]
    return {
        "status": "success",
        "source_group": {"id": src_id, "name": group_display_name(source)},
        "new_group": {
            "id": str(new_id),
            "name": new_name,
            "invite_code": new_group.get("inviteCode") or new_group.get("invite"),
        },
        "members": {
            "total_in_source": len(member_ids),
            "added_on_create": len(initial),
            "added_in_batches": len(remaining),
            "failed_batches": len(failed_batches),
        },
        "batch_results": add_results,
        "note": (
            "WhatsApp only adds contacts you can add to groups. "
            "Some members may fail if they restrict invites or are not in your contacts."
        ),
    }
