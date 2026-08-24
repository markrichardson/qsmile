# Rhiza Upgrade Notes

## Current Situation

- **Current Version**: v1.3.2 (template.yml) / v0.10.4 (actually synced)
- **Latest Version**: v1.6.0
- **Problem**: Latest rhiza requires Claude Code plugin, which we don't have (using GitHub Copilot)
- **Status**: rhiza-cli is archived/retired (no longer maintained)

## Options

### Option 1: Stay on Current Version ✅ RECOMMENDED
**Pros**: No work, everything works
**Cons**: Missing new features from v1.4.0-v1.6.0

Keep current configuration. The templates work fine and are well-tested.

### Option 2: Manual Sync to v1.6.0
**Pros**: Get latest features
**Cons**: Manual process, no automatic updates

#### Steps for Manual Sync:

1. **Clone latest rhiza template**:
   ```bash
   cd /tmp
   git clone https://github.com/jebel-quant/rhiza.git
   cd rhiza
   git checkout v1.6.0
   ```

2. **Review what chebpy uses** (our reference):
   - Profile: `github-project`  
   - Templates: `devcontainer`, `github-paper`
   - Excludes: `.github/CONFIG.md`

3. **Manually copy updated files**:
   Look at the bundles you need and copy specific files:
   ```bash
   # Example - copy workflow files
   cp rhiza/bundles/github/.github/workflows/*.yml \
      ~/git-repos/qsmile/.github/workflows/
   
   # Copy makefile components
   cp -r rhiza/bundles/core/.rhiza/make.d/* \
      ~/git-repos/qsmile/.rhiza/make.d/
   ```

4. **Review and commit**:
   ```bash
   cd ~/git-repos/qsmile
   git diff  # Review changes
   git add -p  # Stage selectively
   git commit -m "chore: manual sync to rhiza v1.6.0"
   ```

5. **Update template.yml**:
   ```yaml
   repository: "jebel-quant/rhiza"
   ref: "v1.6.0"
   
   profiles:
     - github-project
   
   templates:
     - devcontainer
     - github-devcontainer
     - marimo
   ```

### Option 3: Use Archived rhiza-cli ⚠️ LIMITED
**Status**: Still works! Tested with v0.18.0 against rhiza v1.3.2
**Pros**: Automated syncing still works for older rhiza versions
**Cons**: 
- Archived/unmaintained (no future updates)
- Only works with rhiza versions before v1.6.0 (pre-Claude Code requirement)
- May break in the future

#### Using rhiza-cli:

```bash
# Preview what would change (dry-run)
uvx rhiza@0.18.0 sync --strategy diff

# Actually perform the sync (requires clean git tree)
uvx rhiza@0.18.0 sync

# Or sync to a specific branch
uvx rhiza@0.18.0 sync --target-branch update-rhiza
```

**Important**: This can help you sync to v1.3.2 (your current config) but cannot upgrade to v1.6.0 which requires Claude Code.

### Option 4: Pin to Last CLI-Compatible Version
Stay on v1.3.2 or find the last rhiza version that worked with rhiza-cli.
This gives you a stable base without manual updates.

## Key Changes in v1.4.0 - v1.6.0

Based on chebpy's config, the main change is:
- **github-paper bundle**: New workflow for LaTeX paper compilation
- Various bugfixes and improvements to workflows

## Recommendation for qsmile

**VERDICT**: **Stay on v1.3.2** (Option 1)

**Reasoning**:
1. ✅ Your current setup works fine
2. ✅ v1.3.2 → v1.6.0 changes are mostly about `github-paper` bundle (LaTeX compilation)
3. ✅ You're not using the `github-paper` bundle
4. ❌ Manual syncing is tedious and error-prone
5. ❌ rhiza-cli is deprecated and can't upgrade you to v1.6.0 anyway
6. ❌ You'd need Claude Code to use v1.6.0+ properly

**Action items**:
- ✅ Keep `.rhiza/template.yml` at `ref: "v1.3.2"`
- ✅ Use `uvx rhiza@0.18.0 sync` if you need to re-sync the v1.3.2 templates
- 🔮 Revisit if GitHub Copilot adds rhiza support (unlikely)
- 🔮 Or when you actually need features from v1.6.0+

## Future Strategy

When GitHub Copilot adds support for rhiza (unlikely) or if you switch to Claude Code:
- You can use `/rhiza:update` for automatic syncing
- Until then, manual syncs or staying put are your options

## References

- Rhiza main repo: https://github.com/jebel-quant/rhiza
- Archived CLI: https://github.com/jebel-quant/rhiza-cli (read-only)
- Chebpy reference: https://github.com/chebpy/chebpy/blob/master/.rhiza/template.yml
