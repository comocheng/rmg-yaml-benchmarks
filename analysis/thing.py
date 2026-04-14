# functions from rmg for inspiration 

def process_profile_stats(stats_file, log_file):
    import pstats

    out_stream = Tee(sys.stdout, open(log_file, "a"))  # print to screen AND append to RMG.log
    print("=" * 80, file=out_stream)
    print("Profiling Data".center(80), file=out_stream)
    print("=" * 80, file=out_stream)
    stats = pstats.Stats(stats_file, stream=out_stream)
    stats.strip_dirs()
    print("Sorted by internal time", file=out_stream)
    stats.sort_stats("time")
    stats.print_stats(25)
    stats.print_callers(25)
    print("Sorted by cumulative time", file=out_stream)
    stats.sort_stats("cumulative")
    stats.print_stats(25)
    stats.print_callers(25)
    stats.print_callees(25)


def make_profile_graph(stats_file, force_graph_generation=False):
    """
    Uses gprof2dot to create a graphviz dot file of the profiling information.

    This requires the gprof2dot package available via `pip install gprof2dot`.
    Render the result using the program 'dot' via a command like
    `dot -Tps2 input.dot -o output.ps2`.

    Rendering the ps2 file to pdf requires an external pdf converter
    `ps2pdf output.ps2` which produces a `output.ps2.pdf` file.

    Will only generate a graph if a display is present as errors can occur otherwise. If `force_graph_generation` is
    True then the graph generation will be attempted either way
    """
    # Making the profile graph requires a display. See if one is available first
    display_found = False

    try:
        display_found = bool(os.environ["DISPLAY"])
    except KeyError:  # This means that no display was found
        pass

    if display_found or force_graph_generation:
        try:
            from gprof2dot import (
                SAMPLES,
                TIME,
                TIME_RATIO,
                TOTAL_TIME,
                TOTAL_TIME_RATIO,
                DotWriter,
                PstatsParser,
                themes,
            )
        except ImportError:
            logging.warning("Trouble importing from package gprof2dot. Unable to create a graph of the profile statistics.")
            logging.warning("Try getting the latest version with something like `pip install --upgrade gprof2dot`.")
            return
        import subprocess

        # create an Options class to mimic optparser output as much as possible:
        class Options(object):
            pass

        options = Options()
        options.node_thres = 0.8
        options.edge_thres = 0.1
        options.strip = False
        options.show_samples = False
        options.root = ""
        options.leaf = ""
        options.wrap = True

        theme = themes["color"]  # bw color gray pink
        theme.fontname = "ArialMT"  # default "Arial" leads to PostScript warnings in dot (on Mac OS)
        parser = PstatsParser(stats_file)
        profile = parser.parse()

        dot_file = stats_file + ".dot"
        output = open(dot_file, "wt")
        dot = DotWriter(output)
        dot.strip = options.strip
        dot.wrap = options.wrap

        # Add both total time and self time in seconds to the graph output
        dot.show_function_events = [TOTAL_TIME, TOTAL_TIME_RATIO, TIME, TIME_RATIO]

        if options.show_samples:
            dot.show_function_events.append(SAMPLES)

        profile = profile
        profile.prune(options.node_thres / 100.0, options.edge_thres / 100.0, [], False)

        if options.root:
            root_id = profile.getFunctionId(options.root)
            if not root_id:
                sys.stderr.write("root node " + options.root + " not found (might already be pruned : try -E0 -n0 flags)\n")
                sys.exit(1)
            profile.prune_root(root_id)
        if options.leaf:
            leaf_id = profile.getFunctionId(options.leaf)
            if not leaf_id:
                sys.stderr.write("leaf node " + options.leaf + " not found (maybe already pruned : try -E0 -n0 flags)\n")
                sys.exit(1)
            profile.prune_leaf(leaf_id)

        dot.graph(profile, theme)

        output.close()

        try:
            subprocess.check_call(["dot", "-Tps2", dot_file, "-o", "{0}.ps2".format(dot_file)])
        except subprocess.CalledProcessError:
            logging.error("Error returned by 'dot' when generating graph of the profile statistics.")
            logging.info("To try it yourself:\n     dot -Tps2 {0} -o {0}.ps2".format(dot_file))
        except OSError:
            logging.error("Couldn't run 'dot' to create graph of profile statistics. Check graphviz is installed properly " "and on your path.")
            logging.info("Once you've got it, try:\n     dot -Tps2 {0} -o {0}.ps2".format(dot_file))

        try:
            subprocess.check_call(["ps2pdf", "{0}.ps2".format(dot_file), "{0}.pdf".format(dot_file)])
        except OSError:
            logging.error("Couldn't run 'ps2pdf' to create pdf graph of profile statistics. Check that ps2pdf converter " "is installed.")
            logging.info("Once you've got it, try:\n     pd2pdf {0}.ps2 {0}.pdf".format(dot_file))
        else:
            logging.info("Graph of profile statistics saved to: \n {0}.pdf".format(dot_file))

    else:
        logging.warning(
            "Could not find a display, which is required in order to generate the profile graph. This "
            "is likely due to this job being run on a remote server without performing X11 forwarding "
            "or running the job through a job manager like SLURM.\n\n The graph can be generated later "
            "by running with the postprocessing flag `rmg.py -P input.py` from any directory/computer "
            "where both the input file and RMG.profile file are located and a display is available.\n\n"
            "Note that if the postprocessing flag is specified, this will force the graph generation "
            "regardless of if a display was found, which could cause this program to crash or freeze."
        )
