def rutina(lugar, banos=False):
    tareas = []
    for hora, apertura in [('08:00', True), ('15:00', False), ('18:00', True), ('22:00', False)]:
        horario = f'{hora}-{hora}'
        tareas.extend([
            (horario, 'Abrir portón.' if apertura else 'Cerrar portón.', 'Culto'),
            (horario, f'{"Encender" if apertura else "Apagar"} luces de {lugar} y salones.', 'Culto'),
        ])
        if banos:
            tareas.append((horario, 'Abrir baños.' if apertura else 'Cerrar baños.', 'Culto'))
    return tareas


DOMINGO = {
    'PUESTO 1': rutina('auditorio'),
    'PUESTO 3': rutina('bodegas', banos=True),
}
