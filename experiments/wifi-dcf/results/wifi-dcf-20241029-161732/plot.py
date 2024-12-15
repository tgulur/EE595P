plt.figure()
    plt.title('Collision Percentage vs. Number of Stations')
    plt.xlabel('Number of STAs')
    plt.ylabel('Collision Probability')
    plt.grid()
    # plt.xscale('log')
    throughput = []
    with open('wifi-dcf.dat', 'r') as f:
        lines = f.readlines()
        for line in lines:
            tokens = line.split(',')
            throughput.append((tokens[1]))
    plt.plot(range(1,), throughput, marker='o')
    plt.savefig(os.path.join(results_dir, 'wifi-dcf.png'))