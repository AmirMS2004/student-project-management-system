from io import BytesIO
from zipfile import ZipFile


def test_owner_professor_can_export_zip(client, professor, approved_project):
    r = client.get(
        f"/api/projects/{approved_project['id']}/export-zip",
        headers=professor["headers"],
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"

    zf = ZipFile(BytesIO(r.content))
    assert "پرونده-پروژه.pdf" in zf.namelist()


def test_unrelated_student_cannot_export_zip(client, other_student, approved_project):
    r = client.get(
        f"/api/projects/{approved_project['id']}/export-zip",
        headers=other_student["headers"],
    )
    assert r.status_code == 403


def test_zip_includes_uploaded_files_from_every_source(
    client, professor, student, approved_project
):
    project_id = approved_project["id"]

    client.post(
        f"/api/projects/{project_id}/reports",
        data={"content": "گزارش با پیوست"},
        files={"file": ("report.txt", b"report content", "text/plain")},
        headers=student["headers"],
    )
    client.post(
        f"/api/projects/{project_id}/files",
        data={"description": "فایل نیازمندی‌ها"},
        files={"file": ("required.txt", b"required content", "text/plain")},
        headers=professor["headers"],
    )
    client.post(
        f"/api/projects/{project_id}/brief-file",
        files={"file": ("brief.txt", b"brief content", "text/plain")},
        headers=professor["headers"],
    )

    r = client.get(
        f"/api/projects/{project_id}/export-zip", headers=professor["headers"]
    )
    assert r.status_code == 200
    zf = ZipFile(BytesIO(r.content))
    names = zf.namelist()

    assert "پرونده-پروژه.pdf" in names
    assert any(n.startswith("گزارش‌ها/") and n.endswith("report.txt") for n in names)
    assert any(n.startswith("فایل‌ها/") and n.endswith("required.txt") for n in names)
    assert any(n.startswith("فایل-توضیحات-تکمیلی/") and n.endswith("brief.txt") for n in names)

    assert zf.read([n for n in names if n.endswith("report.txt")][0]) == b"report content"
