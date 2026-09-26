import json
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.backup import BackupService

router = APIRouter(prefix="/backup", tags=["Backup, Import & Export"])

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/export-full")
def export_full_database(db: DatabaseSession) -> Response:
    """Exports a full snapshot of the entire database in JSON format."""
    service = BackupService(db)
    data = service.export_full_database()
    filename = f"gys_crm_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    content = json.dumps(data, indent=2, ensure_ascii=False)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import-full")
async def import_full_database(
    request: Request,
    db: DatabaseSession,
) -> dict[str, Any]:
    """Restores/imports a full JSON database snapshot via file upload or JSON payload."""
    service = BackupService(db)
    content_type = request.headers.get("content-type", "")

    data = None
    if "multipart/form-data" in content_type:
        form = await request.form()
        uploaded_file = form.get("file")
        if uploaded_file and hasattr(uploaded_file, "read"):
            content = await uploaded_file.read()
            try:
                data = json.loads(content.decode("utf-8"))
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Archivo JSON corrupto o inválido: {e}",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se encontró el archivo de respaldo en el formulario.",
            )
    else:
        try:
            data = await request.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cuerpo JSON inválido: {e}",
            )

    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los datos de respaldo están vacíos.",
        )

    return service.import_full_database(data)


@router.get("/export-clients-csv")
def export_clients_csv(db: DatabaseSession) -> Response:
    """Exports all clients in standard CSV format (compatible with Microsoft Excel)."""
    service = BackupService(db)
    csv_text = service.export_clients_csv()
    filename = f"clientes_garbo_y_salero_{datetime.now().strftime('%Y%m%d')}.csv"

    # Add UTF-8 BOM so Excel automatically recognizes Spanish characters and accents
    bom_content = "\ufeff" + csv_text
    return Response(
        content=bom_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/template-clients-csv")
def get_clients_csv_template() -> Response:
    """Returns an empty template CSV with example rows for easy bulk importing."""
    sample_csv = (
        "\ufeffNombres,Apellidos,DNI,WhatsApp,Telefono,Email,Anio_Nacimiento,Es_Menor,Nombre_Apoderado,Telefono_Apoderado,Parentesco_Apoderado,DNI_Apoderado,Sede_Preferida,Estado,Origen_Captacion,Referido_Por_Nombre,Referido_Por_Telefono,Notas\n"
        "María José,Flores Quispe,78912345,+51 987654321,+51 987654321,maria@ejemplo.pe,2016,SI,Rosa Quispe,+51 987654321,Madre,09876543,Los Olivos,active,whatsapp,Carmen Torres,+51 999888777,Turno tarde sábados\n"
        "Carlos Eduardo,Mendoza Vega,70123456,+51 955444333,,carlos@ejemplo.pe,2002,NO,,,,,Comas,interested,instagram,,,Preguntó por clases particulares\n"
    )
    return Response(
        content=sample_csv,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="plantilla_clientes_garbo_y_salero.csv"'},
    )


@router.post("/import-clients-csv")
async def import_clients_csv(
    request: Request,
    db: DatabaseSession,
) -> dict[str, Any]:
    """Bulk imports clients from a CSV spreadsheet via file upload or raw CSV text."""
    service = BackupService(db)
    content_type = request.headers.get("content-type", "")

    raw_content = ""
    if "multipart/form-data" in content_type:
        form = await request.form()
        uploaded_file = form.get("file")
        if uploaded_file and hasattr(uploaded_file, "read"):
            file_bytes = await uploaded_file.read()
            try:
                raw_content = file_bytes.decode("utf-8-sig")
            except UnicodeDecodeError:
                raw_content = file_bytes.decode("latin-1")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se encontró el archivo CSV en el formulario.",
            )
    else:
        body_bytes = await request.body()
        try:
            raw_content = body_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            raw_content = body_bytes.decode("latin-1")

    if not raw_content or not raw_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El contenido CSV está vacío.",
        )

    result = service.import_clients_csv(raw_content)
    if result.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Error al procesar el archivo CSV."),
        )
    return result
