/// Existing behavior, not an approved verification requirement.
pub fn prefix_sum(buffer: &[u8], length: usize) -> u32 {
    let mut total = 0u32;
    for i in 0..length {
        total += buffer[i] as u32;
    }
    total
}

#[test]
fn sums_a_prefix() {
    assert_eq!(prefix_sum(&[1, 2, 3], 2), 3);
}
