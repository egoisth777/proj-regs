# Test Spec: manual/ Documentation

### Test: All documentation files exist

**Type:** Unit
**Covers behavior:** Documentation index exists, All subsystems documented
**Setup:** Check filesystem for expected files
**Assert:** All 9 files exist under manual/

### Test: Cross-references resolve

**Type:** Unit
**Covers behavior:** Cross-references are valid
**Setup:** Parse markdown links in all manual files
**Assert:** All relative links point to existing files
