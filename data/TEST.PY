import sqlite3

DB_PATH = "jobs.db"  # adjust if needed


def print_jobs(limit=10):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get columns
    cur.execute("PRAGMA table_info(jobs)")
    cols = [c[1] for c in cur.fetchall()]
    print("Columns:", cols)

    # Select rows
    query = "SELECT * FROM jobs"
    params = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)

    cur.execute(query, params)
    rows = cur.fetchall()

    print(f"\nTotal rows fetched: {len(rows)}")
    for i, row in enumerate(rows, start=1):
        print(f"\n========== ROW {i} ==========")
        for col, val in zip(cols, row):
            text = "" if val is None else str(val)
            # Optional: truncate huge blobs so your terminal doesn't die
            if len(text) > 2000:
                text = text[:2000] + "... [truncated]"
            print(f"{col}: {text}")

    conn.close()


if __name__ == "__main__":
    print_jobs(limit=10)  # set to None to print everything
