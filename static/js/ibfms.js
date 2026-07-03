// ---------------------------
// Reloj
// ---------------------------

function actualizarHora(){

    const ahora = new Date();

    const fecha = document.getElementById("fecha");
    const hora = document.getElementById("hora");

    if(fecha){
        fecha.innerHTML = ahora.toLocaleDateString();
    }

    if(hora){
        hora.innerHTML = ahora.toLocaleTimeString();
    }

}

setInterval(actualizarHora,1000);

actualizarHora();


// ---------------------------
// Modo oscuro
// ---------------------------

const interruptor = document.getElementById("modoOscuro");

if(interruptor){

    if(localStorage.getItem("tema")=="oscuro"){

        document.body.classList.add("dark-mode");

        interruptor.checked = true;

    }

    interruptor.addEventListener("change",function(){

        if(this.checked){

            document.body.classList.add("dark-mode");

            localStorage.setItem("tema","oscuro");

        }else{

            document.body.classList.remove("dark-mode");

            localStorage.setItem("tema","claro");

        }

    });

}