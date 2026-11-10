# Installing these skills

## Three steps

1. **Add the cluster as a compute target.** In Claude Science: **Compute → add SSH
   host** → `biologin-0.igb.illinois.edu`, your IGB username, your SSH key. This cannot
   come from a skill; it is app configuration you do once.

   `biologin-0` is the **Biocluster 4** login node. If you have an older entry pointing
   at `biologin-3`, that was Biocluster 3 and it is gone — update it, or everything in
   these skills will be wrong for you. `/home` is shared across login nodes, so your
   `~/.ssh/authorized_keys` carries over; a "Permission denied (publickey)" on the new
   host is an authentication problem, not a DNS one.

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

A correct answer means the hub skill loaded and your partition facts are recorded. The
answer should be **`gpu`** — two **A40s** (47.7 GB each) per node, a 250 GB node memory
ceiling — and nothing else.

`gpu` and `normal` are the two partitions an ordinary account can submit to. `sinfo -a`
lists fifteen, several of them sitting idle advertising GPUs and large-memory nodes.
**If the agent offers you any partition other than those two, that is a bug worth
reporting** — the rest appear in `sinfo` but reject your jobs, and an idle node you
cannot submit to is not capacity. The reliable access test is that
`scontrol show partition <name>` returns *empty* for a partition you cannot use.

A second useful check, because it is the most expensive thing to get wrong:

> *"I need to BLAST some sequences against nr on igb. How do I get the database?"*

The answer should be `module load ncbi-blastdb/20260622` and a subdirectory of
`$EBROOTNCBIMINBLASTDB` — **not** a download. If the agent proposes downloading nr, the
reference-data skill did not load.

## Read this before you trust anything here

Every claim in these skills carries a confidence tier, and **you should treat them
differently**:

- **Tier A — someone ran it on this cluster.** The command shown is the one that worked,
  with real timings. Follow it.
- **Tier B — the module exists and the invocation comes from `module show` or IGB's
  docs**, but nobody has run it here. A good starting point.
- **Tier C — the module is installed, and that is all we know.** The invocation is
  informed guesswork. Expect it to be subtly wrong.

**Why the distinction is not pedantry.** Verification sweeps have repeatedly found
claims that were *wrong* rather than merely unverified:

- reference databases whose module sets a path that **does not exist**
  (`/home/mirrors` — the real directory is `/home/mirror`, singular). Four of the 29 are
  still like this on Biocluster 4;
- a GPU preflight check using `nvidia-smi`, which was **not on `PATH`** on Biocluster 3
  compute nodes and would have aborted every GPU job in the lab;
- a PyTorch build that passes `torch.cuda.is_available()` and then **crashes** on the
  first GPU operation because it has no kernels for the card.

Assume the remaining tier C rows contain errors of the same kind, and read them as a
starting point rather than an instruction.

**And note how much the Biocluster 4 migration invalidated.** Four carefully-verified
Biocluster 3 facts are now reversed: conda went from unusable to working, `nvidia-smi`
from absent to present, TensorFlow's GPU pairing from fixable to broken, and `/scratch`
from present-but-empty to non-existent. Knowledge about a cluster has a short half-life.

## How a tier C claim becomes tier A — this needs you

It cannot happen from a desk. Tier C claims are about tools producing correct output on
real input; the only thing that settles one is **running it on the cluster with your own
data**.

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

The inventory is a snapshot: **173 modules, 212 versions** (names re-counted 2026-11-09; 209 versions on 2026-10-31) on
`biologin-0`. After any cluster change, re-take it:

    module avail 2>&1 | tr -s ' \t' '\n' | grep -E '^[A-Za-z0-9._+-]+/[A-Za-z0-9]' | sort -u

Comparing that list against the [IGB Applications
page](https://help.igb.illinois.edu/Biocluster_Applications) is what found the 29
undocumented database modules in the first place.
