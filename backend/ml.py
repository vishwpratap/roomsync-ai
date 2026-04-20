"""
RoomSync AI - K-Means Clustering Module
Groups users into lifestyle clusters using preferences and behavioral traits.
"""

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from db import execute_query, execute_update

# Features used for clustering (preferences + traits when available)
PREF_FEATURES = ["sleep", "cleanliness", "noise", "smoking", "social"]
TRAIT_FEATURES = ["cleanliness_tolerance", "noise_tolerance", "social_tolerance", "conflict_style", "flexibility"]
N_CLUSTERS = 3

CLUSTER_LABELS = {
    0: "Quiet & Organized",
    1: "Social & Flexible",
    2: "Balanced Lifestyle",
}


def fetch_user_features():
    """Fetch all users' clustering features (preferences + traits) from the database."""
    query = """
        SELECT u.id, p.sleep, p.cleanliness, p.noise, p.smoking, p.social,
               t.cleanliness_tolerance, t.noise_tolerance, t.social_tolerance,
               t.conflict_style, t.flexibility
        FROM users u
        JOIN preferences p ON u.id = p.user_id
        LEFT JOIN user_traits t ON u.id = t.user_id
        ORDER BY u.id
    """
    rows = execute_query(query, fetch_all=True)
    return rows


def run_clustering():
    """
    Run K-Means clustering on all users.
    Updates cluster_id in the users table.
    """
    rows = fetch_user_features()

    if not rows or len(rows) < N_CLUSTERS:
        print(f"[ML] Not enough users for clustering ({len(rows) if rows else 0}/{N_CLUSTERS})")
        return None

    user_ids = [row["id"] for row in rows]
    features = []
    for row in rows:
        feat = [row[f] for f in PREF_FEATURES]
        # Add trait features if available (default to 3 if NULL)
        for tf in TRAIT_FEATURES:
            feat.append(row[tf] if row[tf] is not None else 3)
        features.append(feat)

    features = np.array(features)

    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)

    n_clusters = min(N_CLUSTERS, len(rows))
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(features_scaled)

    for user_id, cluster_id in zip(user_ids, labels):
        execute_update(
            "UPDATE users SET cluster_id = %s WHERE id = %s",
            (int(cluster_id), user_id)
        )

    # Optional: upgrade generic roommate_type using cluster signal.
    # We avoid overwriting specific labels (e.g. "Night Owl", "Disciplined Minimalist").
    # This satisfies "traits + cluster" labeling while keeping existing logic intact.
    try:
        user_rows = execute_query(
            "SELECT id, roommate_type, cluster_id FROM users WHERE id IN (" + ",".join(["%s"] * len(user_ids)) + ")",
            tuple(user_ids),
            fetch_all=True,
        )
        for u in user_rows or []:
            if not u.get("cluster_id") and u.get("cluster_id") != 0:
                continue
            current = (u.get("roommate_type") or "").strip()
            if current in ("", "Balanced Roommate", "Balanced Lifestyle", "Unknown Cluster"):
                cluster_label = get_cluster_label(int(u["cluster_id"]))
                execute_update(
                    "UPDATE users SET roommate_type = %s WHERE id = %s",
                    (cluster_label, u["id"]),
                )
    except Exception as e:
        print(f"[ML] Roommate-type upgrade skipped: {e}")

    print(f"[ML] Clustering complete. {len(user_ids)} users assigned to {n_clusters} clusters.")
    print(f"[ML] Cluster distribution: {dict(zip(*np.unique(labels, return_counts=True)))}")

    return {
        "users_clustered": len(user_ids),
        "n_clusters": n_clusters,
        "centroids": kmeans.cluster_centers_.tolist(),
        "labels": {uid: int(lbl) for uid, lbl in zip(user_ids, labels)},
    }


def get_cluster_label(cluster_id: int) -> str:
    """Get human-readable label for a cluster."""
    return CLUSTER_LABELS.get(cluster_id, "Unknown Cluster")
