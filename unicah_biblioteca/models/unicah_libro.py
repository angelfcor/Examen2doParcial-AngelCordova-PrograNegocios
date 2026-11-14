from odoo import api, fields, models


class UnicahLibro(models.Model):
    _name = "unicah.libro"
    _description = "Libro de la biblioteca"

    name = fields.Char(string="Título", required=True)
    autor = fields.Char(string="Autor")
    isbn = fields.Char(string="ISBN")
    copias_totales = fields.Integer(string="Copias totales", default=1)
    prestamo_ids = fields.One2many("unicah.prestamo", "libro_id", string="Préstamos")
    copias_disponibles = fields.Integer(
        string="Copias disponibles",
        compute="_compute_copias_disponibles",
    )

    @api.depends("copias_totales", "prestamo_ids.estado")
    def _compute_copias_disponibles(self):
        for libro in self:
            activos = len(libro.prestamo_ids.filtered(lambda p: p.estado == "prestado"))
            libro.copias_disponibles = libro.copias_totales - activos