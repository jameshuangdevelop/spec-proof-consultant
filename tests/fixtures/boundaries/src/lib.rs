unsafe extern "C" {
    fn foreign_copy();
}

pub unsafe fn bridge(buffer: &mut [u8]) {
    foreign_copy();
    buffer[0] = 1;
}
