#include <iostream>
#include <fstream>
#include <string>
#include <chrono> // Para obtener la hora actual
#include <ctime>  // Para formatear la hora

// Función para guardar un registro en un archivo de texto
// Esta es la función que será accesible desde Python
extern "C" __declspec(dllexport)
void guardar_registro_c(const char* dato) {
    std::ofstream outfile;
    // Abre el archivo "metadata.db" en modo de añadir (std::ios_base::app)
    // Se crea si no existe.
    outfile.open("metadata.db", std::ios_base::app);

    if (outfile.is_open()) {
        // Obtener la hora actual
        auto now = std::chrono::system_clock::now();
        auto in_time_t = std::chrono::system_clock::to_time_t(now);
        // Formatear la hora a una cadena legible
        std::string s_time = std::ctime(&in_time_t);
        s_time.pop_back(); // Eliminar el '\n' final que ctime añade

        // Escribir el registro con la marca de tiempo
        outfile << "[" << s_time << "] " << dato << std::endl;
        outfile.close();
        // Opcional: imprimir en la consola C++ para depuración (comentar en producción)
        // std::cout << "Dato registrado en metadata.db: " << dato << std::endl;
    } else {
        // Opcional: imprimir error en la consola C++ si no se puede abrir el archivo
        // std::cerr << "Error: No se pudo abrir 'metadata.db' para escribir." << std::endl;
    }
}
