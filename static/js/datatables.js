
$(document).ready(function () {

    const idiomaEspanol = {
        url: "https://cdn.datatables.net/plug-ins/1.13.8/i18n/es-ES.json"
    };

    const tablas = [
        "#tablaVisitantes",
        "#tablaEmpleados",
        "#tablaBitacora",
        "#tablaIncidentes",
        "#tablaActividades",
        "#tablaVIP",
        "#tablaUsuarios",
        "#tablaControlVehiculos"
    ];

    function instalarBarraSuperior(zona) {
        if (!zona) return;

        const cuerpo = zona.querySelector(".dataTables_scrollBody");
        const encabezado = zona.querySelector(".dataTables_scrollHead");

        if (!cuerpo || !encabezado) return;

            // Eliminar barras superiores duplicadas dentro de esta tabla
        const barrasExistentes = zona.querySelectorAll(
            ":scope > .barra-scroll-superior"
        );

        for (let i = 1; i < barrasExistentes.length; i++) {
            barrasExistentes[i].remove();
        }

        let barra = zona.querySelector(
            ":scope > .barra-scroll-superior"
        );
        
        if (!barra) {
            barra = document.createElement("div");
            barra.className = "barra-scroll-superior";

            const interior = document.createElement("div");
            interior.className = "barra-scroll-interior";
            barra.appendChild(interior);

            zona.insertBefore(barra, encabezado);

            let sincronizando = false;

            barra.addEventListener("scroll", function () {
                if (sincronizando) return;
                sincronizando = true;
                cuerpo.scrollLeft = barra.scrollLeft;
                sincronizando = false;
            });

            cuerpo.addEventListener("scroll", function () {
                if (sincronizando) return;
                sincronizando = true;
                barra.scrollLeft = cuerpo.scrollLeft;
                sincronizando = false;
            });
        }

        const interior = barra.firstElementChild;

        function actualizar() {
            interior.style.width = cuerpo.scrollWidth + "px";

            const necesitaScroll =
                cuerpo.scrollWidth > cuerpo.clientWidth + 2;

            barra.style.display = necesitaScroll ? "block" : "none";
            barra.scrollLeft = cuerpo.scrollLeft;
        }

        actualizar();

        if (barra._observador) {
            barra._observador.disconnect();
        }

        if ("ResizeObserver" in window) {
            barra._observador = new ResizeObserver(actualizar);
            barra._observador.observe(cuerpo);

            if (cuerpo.firstElementChild) {
                barra._observador.observe(cuerpo.firstElementChild);
            }
        }
    }

    tablas.forEach(function (selector) {
        const tabla = $(selector);

        if (!tabla.length) return;

        if (!$.fn.DataTable.isDataTable(selector)) {
            tabla.DataTable({
                responsive: false,
                scrollX: true,
                autoWidth: false,
                pageLength: 10,
                lengthMenu: [
                    [10, 25, 50, 100, -1],
                    [10, 25, 50, 100, "Todos"]
                ],
                language: idiomaEspanol,
                initComplete: function () {
                    const zona = this.api()
                        .table()
                        .container()
                        .querySelector(".dataTables_scroll");

                    const envoltura = this.api().table().container()
                        .closest(".table-responsive");

                    if (envoltura) {
                        envoltura.dataset.scrollManaged = "true";
                    }

                    instalarBarraSuperior(zona);
                },
                drawCallback: function () {
                    const zona = this.api()
                        .table()
                        .container()
                        .querySelector(".dataTables_scroll");

                    instalarBarraSuperior(zona);
                }
            });
        } else {
            const api = tabla.DataTable();
            instalarBarraSuperior(
                api.table().container().querySelector(".dataTables_scroll")
            );
        }
    });

    // Tablas normales, sin DataTables
    document.querySelectorAll(".table-responsive").forEach(function (contenedor) {

        
if (
    contenedor.dataset.scrollManaged === "true" ||
    contenedor.querySelector(".dataTables_wrapper") ||
    contenedor.querySelector(
        "#tablaVisitantes, #tablaEmpleados, #tablaBitacora, " +
        "#tablaIncidentes, #tablaActividades, #tablaVIP, " +
        "#tablaUsuarios, #tablaControlVehiculos"
    )
) {
    return;
}


        const tabla = contenedor.querySelector("table");
        if (!tabla || contenedor.dataset.topScrollReady === "true") return;

        contenedor.dataset.topScrollReady = "true";

        const barra = document.createElement("div");
        barra.className = "barra-scroll-superior";

        const interior = document.createElement("div");
        interior.className = "barra-scroll-interior";
        barra.appendChild(interior);

        contenedor.parentNode.insertBefore(barra, contenedor);

        let sincronizando = false;

        barra.addEventListener("scroll", function () {
            if (sincronizando) return;
            sincronizando = true;
            contenedor.scrollLeft = barra.scrollLeft;
            sincronizando = false;
        });

        contenedor.addEventListener("scroll", function () {
            if (sincronizando) return;
            sincronizando = true;
            barra.scrollLeft = contenedor.scrollLeft;
            sincronizando = false;
        });

        function actualizar() {
            interior.style.width = tabla.scrollWidth + "px";

            barra.style.display =
                tabla.scrollWidth > contenedor.clientWidth + 2
                    ? "block"
                    : "none";

            barra.scrollLeft = contenedor.scrollLeft;
        }

        actualizar();

        if ("ResizeObserver" in window) {
            const observador = new ResizeObserver(actualizar);
            observador.observe(contenedor);
            observador.observe(tabla);
        }
    });

});
