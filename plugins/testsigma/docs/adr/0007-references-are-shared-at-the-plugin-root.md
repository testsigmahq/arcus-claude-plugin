# References are shared at the plugin root, not bundled per skill

The plugin's reference documents live in one `references/` directory at the
plugin root, and every skill points into it with `${CLAUDE_PLUGIN_ROOT}`. Claude
Code's documented skill layout puts a skill's `references/` *inside* that skill's
own directory, so this is a deliberate deviation, and it is the reason a bare
`references/foo.md` resolves to nothing here.

## Considered Options

**Per-skill references, as the convention shows.** Rejected. Every reference in
this plugin is read by more than one skill: the element-resolution procedure by
`map` and `resolve-elements`, the asking rules by all five, the check order by
two skills and the command, the Migration Directory's file set by everything.
Bundling them per skill means one copy per caller, which is the duplication the
whole design exists to prevent — and which had already happened once by prose
alone, without the layout encouraging it (see the commit that split
`element-resolution.md` back out of its callers).

**Symlinks from each skill to a shared directory.** Rejected: it satisfies the
convention's shape while keeping one file, but it makes the seam invisible in a
listing and depends on how a plugin is packaged and installed.

**A shared directory at the plugin root.** Chosen. The documented layout already
puts `scripts/` at the plugin root for shared utilities, so a shared directory
beside the components is a sanctioned pattern; this deviates in *which*
directory is shared, not in kind.

## Consequences

**One spelling for every pointer.** Because the references are not
skill-relative, a skill-relative path cannot address them, so every pointer into
the plugin's own files is anchored with `${CLAUDE_PLUGIN_ROOT}`, which Claude
Code substitutes with the plugin's absolute path when a component loads. Three
spellings were in use before this was settled and one of them resolved nowhere,
including on the CLI-probe path of both entry points, where a failed read is a
silently skipped probe rather than an error.

**The anchor also tells the two kinds of path apart.** These documents name
plugin files and Migration Directory files — `residue.md` and `step-map.md` live
in the user's suite. The anchor marks which is which, so a stage cannot read a
file the plugin ships where it meant one the Migration owns.
`tests/test_pointers_resolve.py` enforces the distinction in both directions.
