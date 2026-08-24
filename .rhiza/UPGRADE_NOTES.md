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

### Option 3: Use Archived rhiza-cli (Not Recommended)
The old CLI might still work for older rhiza versions, but:
- It's archived/unmaintained
- May break at any time
- Last release: v0.18.0

If you want to try:
```bash
uvx rhiza@0.18.0 sync --strategy diff  # Preview
uvx rhiza@0.18.0 sync  # Actually sync
```

### Option 4: Pin to Last CLI-Compatible Version
Stay on v1.3.2 or find the last rhiza version that worked with rhiza-cli.
This gives you a stable base without manual updates.

## Key Changes in v1.4.0 - v1.6.0

Based on chebpy's config, the main change is:
- **github-paper bundle**: New workflow for LaTeX paper compilation
- Various bugfixes and improvements to workflows

## Recommendation

**For qsmile**: Use **Option 1** (stay on current version) unless you specifically need:
- The `github-paper` bundle for LaTeX compilation
- Specific bugfixes from newer versions

The cost/benefit of manual syncing doesn't justify the effort for a stable project.

## Future Strategy

When GitHub Copilot adds support for rhiza (unlikely) or if you switch to Claude Code:
- You can use `/rhiza:update` for automatic syncing
- Until then, manual syncs or staying put are your options

## References

- Rhiza main repo: https://github.com/jebel-quant/rhiza
- Archived CLI: https://github.com/jebel-quant/rhiza-cli (read-only)
- Chebpy reference: https://github.com/chebpy/chebpy/blob/master/.rhiza/template.yml
