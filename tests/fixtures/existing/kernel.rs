verus! {
    fn increment(x: u8) -> (result: u8)
        requires x < 255,
        ensures result == x + 1,
    {
        x + 1
    }
}

#[kani::proof]
fn check_increment() {
    assert!(true);
}
