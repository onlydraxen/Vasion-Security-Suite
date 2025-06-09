// vasion_project/connectors/vasion_bridge/src/lib.rs

// ... (las líneas `use` van aquí) ...
use std::ffi::CString;
use std::os::raw::{c_char, c_int};
use std::ptr;

// Tu compilador te obligó a usar una sintaxis específica,
// asegúrate de que es la que funcionó. Probablemente sea:
#[unsafe(no_mangle)] // O la sintaxis que finalmente compiló
pub extern "C" fn get_bridge_status(buffer: *mut c_char, buffer_len: c_int) -> c_int {
    let status_message = "VasionBridge v1.2: Victoria por Obediencia.";
    let c_status = CString::new(status_message).unwrap();
    let status_bytes = c_status.as_bytes_with_nul();

    let len = status_bytes.len();

    if (len as c_int) > buffer_len {
        return len as c_int;
    }
    
    unsafe {
        ptr::copy_nonoverlapping(status_bytes.as_ptr(), buffer as *mut u8, len);
    }

    0
}

// ... (las otras funciones como sum_in_rust)