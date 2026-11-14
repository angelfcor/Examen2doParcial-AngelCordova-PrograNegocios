from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError

DIAS_PRESTAMO = 7
MAX_PRESTAMOS = 3
MULTA_POR_DIA = 5


class UnicahPrestamo(models.Model):
    _name = "unicah.prestamo"
    _description = "Préstamo de libro"

    libro_id = fields.Many2one("unicah.libro", string="Libro", required=True)
    estudiante_id = fields.Many2one(
        "res.partner",
        string="Estudiante",
        required=True,
        domain="[('tipo_cliente', '=', 'estudiante')]",
    )
    fecha_prestamo = fields.Date(
        string="Fecha de préstamo",
        required=True,
        default=fields.Date.context_today,
    )
    fecha_limite = fields.Date(
        string="Fecha límite",
        compute="_compute_fecha_limite",
        store=True,
    )
    fecha_devolucion = fields.Date(string="Fecha de devolución", readonly=True)
    estado = fields.Selection(
        [("prestado", "Prestado"), ("devuelto", "Devuelto")],
        string="Estado",
        default="prestado",
    )
    dias_atraso = fields.Integer(string="Días de atraso", compute="_compute_atraso")
    multa = fields.Float(string="Multa (L)", compute="_compute_atraso")

    @api.depends("fecha_prestamo")
    def _compute_fecha_limite(self):
        for p in self:
            if p.fecha_prestamo:
                p.fecha_limite = p.fecha_prestamo + timedelta(days=DIAS_PRESTAMO)
            else:
                p.fecha_limite = False

    @api.depends("fecha_limite", "fecha_devolucion", "estado")
    def _compute_atraso(self):
        hoy = fields.Date.context_today(self)
        for p in self:
            fin = p.fecha_devolucion or hoy
            atraso = (fin - p.fecha_limite).days if p.fecha_limite else 0
            p.dias_atraso = max(atraso, 0)
            p.multa = p.dias_atraso * MULTA_POR_DIA

    @api.constrains("libro_id", "estudiante_id", "estado")
    def _check_prestamo(self):
        for p in self:
            if p.estado != "prestado":
                continue
            if p.estudiante_id.tipo_cliente != "estudiante":
                raise ValidationError("Solo se puede prestar a clientes de tipo estudiante.")
            activos_libro = self.search_count([
                ("libro_id", "=", p.libro_id.id), ("estado", "=", "prestado")])
            if activos_libro > p.libro_id.copias_totales:
                raise ValidationError("No hay copias disponibles de este libro.")
            activos_estudiante = self.search_count([
                ("estudiante_id", "=", p.estudiante_id.id), ("estado", "=", "prestado")])
            if activos_estudiante > MAX_PRESTAMOS:
                raise ValidationError(
                    f"El estudiante ya tiene {MAX_PRESTAMOS} préstamos activos."
                )

    def action_devolver(self):
        for p in self:
            p.write({
                "estado": "devuelto",
                "fecha_devolucion": fields.Date.context_today(self),
            })