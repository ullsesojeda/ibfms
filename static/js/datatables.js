$(document).ready(function () {

    // =====================================================
    // IDIOMA ESPAÑOL
    // =====================================================

    const idiomaEspanol = {
        url: "https://cdn.datatables.net/plug-ins/1.13.8/i18n/es-ES.json"
    };

    // =====================================================
    // ORDEN CRONOLÓGICO DE FECHAS DD/MM/AAAA
    // =====================================================

    function textoPlano(valor) {
        return $("<div>")
            .html(String(valor == null ? "" : valor))
            .text()
            .trim();
    }

    function convertirFecha(valor) {
        const texto = textoPlano(valor);
        const coincidencia = texto.match(
            /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/
        );

        if (!coincidencia) return 0;

        const dia = parseInt(coincidencia[1], 10);
        const mes = parseInt(coincidencia[2], 10);
        const anio = parseInt(coincidencia[3], 10);

        if (
            !Number.isInteger(dia) ||
            !Number.isInteger(mes) ||
            !Number.isInteger(anio) ||
            dia < 1 || dia > 31 ||
            mes < 1 || mes > 12 ||
            anio < 1
        ) {
            return 0;
        }

        // Número AAAAMMDD para ordenar cronológicamente.
        return anio * 10000 + mes * 100 + dia;
    }

    // Tipo personalizado para DataTables 1.13.x.
    $.fn.dataTable.ext.type.order["fecha-es-pre"] = function (valor) {
        return convertirFecha(valor);
    };

    // =====================================================
    // TABLAS CON DATATABLES
    // =====================================================

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

    // =====================================================
    // BARRA HORIZONTAL SUPERIOR SINCRONIZADA
    // =====================================================

    function instalarBarraSuperior(zona) {
        if (!zona) return;

        const cuerpo = zona.querySelector(".dataTables_scrollBody");
        const encabezado = zona.querySelector(".dataTables_scrollHead");

        if (!cuerpo || !encabezado) return;

        const barras = zona.querySelectorAll(
            ":scope > .barra-scroll-superior"
        );

        for (let i = 1; i < barras.length; i++) {
            barras[i].remove();
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

            barra.style.display =
                cuerpo.scrollWidth > cuerpo.clientWidth + 2
                    ? "block"
                    : "none";

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

    // =====================================================
    // INICIALIZAR CADA TABLA
    // =====================================================

    tablas.forEach(function (selector) {
        const tabla = $(selector);

        if (!tabla.length) return;

        if ($.fn.DataTable.isDataTable(selector)) {
            return;
        }

        // Identificar las columnas cuyo encabezado sea "Fecha".
        const encabezados = tabla.find("thead th").toArray();

        const columnasFecha = [];

        encabezados.forEach(function (th, indice) {
            const titulo = $(th).text().trim().toLowerCase();

            if (titulo === "fecha") {
                columnasFecha.push(indice);
            }
        });

        // Identificar una columna ID, si existe.
        let columnaId = -1;

        encabezados.forEach(function (th, indice) {
            const titulo = $(th).text().trim().toLowerCase();

            if (
                titulo === "id" ||
                titulo === "n.º" ||
                titulo === "número"
            ) {
                columnaId = indice;
            }
        });

        // Forzar el tipo fecha-es en todas las columnas Fecha.
        const definicionesColumnas = columnasFecha.map(function (indice) {
            return {
                targets: indice,
                type: "fecha-es"
            };
        });

        // Mostrar primero la fecha más reciente.
        // Si hay ID, usarlo como segundo criterio descendente.
        const ordenInicial = [];

        if (columnasFecha.length > 0) {
            ordenInicial.push([columnasFecha[0], "desc"]);

            if (columnaId >= 0 && columnaId !== columnasFecha[0]) {
                ordenInicial.push([columnaId, "desc"]);
            }
        }

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

            // Aplicar el orden inicial solo cuando hay columna Fecha.
            order: ordenInicial,

            // Asignación explícita del tipo personalizado.
            columnDefs: definicionesColumnas,

            initComplete: function () {
                const api = this.api();
                const contenedor = api.table().container();

                const envoltura = contenedor.closest(".table-responsive");

                if (envoltura) {
                    envoltura.dataset.scrollManaged = "true";
                }

                instalarBarraSuperior(
                    contenedor.querySelector(".dataTables_scroll")
                );

                api.columns.adjust();
            },

            drawCallback: function () {
                const contenedor = this.api().table().container();

                instalarBarraSuperior(
                    contenedor.querySelector(".dataTables_scroll")
                );
            }
        });
    }); 
        // =====================================================
    // TABLAS NORMALES, SIN DATATABLES
    // =====================================================

    document.querySelectorAll(".table-responsive").forEach(
        function (contenedor) {

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

            if (
                !tabla ||
                contenedor.dataset.topScrollReady === "true"
            ) {
                return;
            }

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
        }
    );

});      