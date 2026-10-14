# Installing these skills

## Three steps

1. **Add the cluster as a compute target.** In Claude Science: **Compute → add SSH
   host** → `biologin-3.igb.illinois.edu`, your IGB username, your SSH key. This cannot
   come from a skill; it is app configuration you do once. As of 2026-10-13 `biologin-3`
   is the only login node that resolves — `biologin-1` and `biologin-2` are gone, and the
   bare alias `biologin.igb.illinois.edu` points at biologin-3's own address, so the name
   you enter makes no practical difference. Use `biologin-3` for clarity.
2. **Import the skills.** **Skills → Import from GitHub** → this repository's URL. You
   should see:

       Imported 7 skills from IGBIllinois/Biocluster-claude
       Skipped: igb-cluster (kernel) - 1 kernel sidecar file(s) excluded

   **That "Skipped" line is expected and nothing is missing.** Imported skills are
   documentation-only, so `skills/igb-cluster/kernel.py` is not installed. Every rule it
   encodes is written out in full in the skill documents.
3. **Record your own partition access.** This differs per account, because IGB grants
   partitions by Unix group — yours is not a colleague's. Ask the agent to run:

       id
       scontrol show partition | grep -E 'PartitionName|AllowGroups|MaxMemPerNode'
       sinfo -o "%.12P %.5D %.5c %.9m %.20G %.11l %.6t"

   and to append the result to `compute_details` for the `igb` target. One read-only
   call; after that every session starts informed.

## Check it worked

Ask for something small:

> *"What GPU partitions can I use on igb, and what's the memory ceiling on each?"*

A correct answer means the hub skill loaded and your partition facts are recorded. On
the account this repo was built from, the answer is `admin` (one RTX A6000, **60 GB**
ceiling, normally idle) and `gpu` (two A40s per node, 250 GB, but 22–32 h queue) — and
the counter-intuitive part is that the *idle* GPU partition has the *smallest* memory on
the cluster, while the 2 TB partition has no GPU at all.

## Read this before you trust anything here

Every claim in these skills carries a confidence tier, and **you should treat them
differently**:

- **Tier A — someone ran it on this cluster.** The command shown is the one that worked,
  with real timings. Follow it.
- **Tier C — the module is installed, and that is all we know.** The invocation is
  informed guesswork. Expect it to be subtly wrong.

(There is no tier B left as of 2026-10-13 — every claim that could be settled by
inspecting the cluster has been.)

**Why the distinction is not pedantry.** Four verification sweeps were run on
2026-10-13, and three of them found claims that were *wrong* rather than merely
unverified:

- five reference databases whose module sets a path that **does not exist**
  (`/home/mirrors` — the real directory is `/home/mirror`, singular);
- a GPU preflight check using `nvidia-smi`, which is **not on `PATH`** on the compute
  nodes and would have aborted every GPU job in the lab;
- `PyTorch/1.12.1`, which passes `torch.cuda.is_available()` and then **crashes** on the
  first GPU operation because it has no kernels for the A6000.

Assume the remaining tier C rows contain errors of the same kind, and read them as a
starting point rather than an instruction.

## How a tier C claim becomes tier A — this needs you

It cannot happen from a desk. Tier C claims are about tools producing correct output on
real input; the only thing that settles one is **running it on the cluster with your own
data**. There is no sweep anyone can do remotely that would promote the 523 NGS modules
or the 10x pipelines.

So when a run of yours works, send back four things:

    the module string you loaded
    the sbatch resources you requested
    the wall time
    MaxRSS from `seff <jobid>`

Either tell the agent in your reply — it will offer to write the correction — or open a
PR on `IGBIllinois/Biocluster-claude`. Four lines from one successful run saves every
person after you a queue wait. **This is the only mechanism by which this repo improves.**

If a skill tells you something that turns out to be wrong, that is worth reporting even
more than a success. The GTDB-Tk entry was corrected exactly that way: a user was told to
download a 110 GB database that was already mirrored on the cluster, the agent checked,
and the skill was fixed.

## Keeping it honest

The inventory is a snapshot: 927 modules, 1795 versions, taken 2026-10-13. After any
cluster change, re-run the wiki-vs-live comparison — it is what found the 29
undocumented database modules in the first place:

    module avail 2>&1 | tr -s ' \t' '\n' | grep -E '^[A-Za-z0-9._+-]+/[A-Za-z0-9]' | sort -u
