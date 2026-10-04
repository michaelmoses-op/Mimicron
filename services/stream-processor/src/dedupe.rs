use lru::LruCache;
use std::num::NonZeroUsize;

pub struct Dedupe {
    seen: LruCache<String, ()>,
}

impl Dedupe {
    pub fn new(capacity: usize) -> Self {
        let cap = NonZeroUsize::new(capacity.max(1)).unwrap();
        Self {
            seen: LruCache::new(cap),
        }
    }

    /// Returns true if this event_id is new (should process).
    pub fn check(&mut self, event_id: &str) -> bool {
        if self.seen.contains(event_id) {
            return false;
        }
        self.seen.put(event_id.to_string(), ());
        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn dedupe_drops_repeats() {
        let mut d = Dedupe::new(10);
        assert!(d.check("a"));
        assert!(!d.check("a"));
        assert!(d.check("b"));
    }
}
