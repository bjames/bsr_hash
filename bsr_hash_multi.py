import ipaddress

from datetime import datetime
from numpy import uint32, bitwise_and, bitwise_xor

from functools import partial
from multiprocessing import Pool

def calculate_hash(rp_address, group, mask):

    """
        implements the hash function from RFC 7761
    """

    result = uint32(bitwise_and(group,mask))
    result = uint32(uint32(1103515245) * uint32(result)) + uint32(12345)
    result = uint32(bitwise_xor(result, rp_address))
    result = uint32(uint32(1103515245) * uint32(result))
    result = uint32(uint32(result) + uint32(12345))
    result = uint32(uint32(result) % uint32(2**31))

    return result


def iter_rp(rp_list, mask, group):

    group_result = []
    group_winner = ''
    winner_val = 0

    for rp in rp_list:

        value = calculate_hash(uint32(rp), uint32(group), mask)
        result = {
            'rp': str(rp),
            'value': value
        }

        if value > winner_val:
            winner_val = value
            group_winner = rp

        group_result.append(result)

    return {
        'group': group,
        'group_results': group_result,
        'group_winner': group_winner
    }


def calculate_winners(results):

    previous_result = ''
    streak = 1
    max_streak = 0
    winner_string = ''
    result_string = ''
    wins = [0] * len(rp_list)

    for group_result in results:

        if group_result['group_winner'] == previous_result:
            streak = streak + 1
        else:
            streak = 1
        if streak >= max_streak:
            max_streak = streak

        result_string = result_string + "{}\t{}\t{}\n".format(str(group_result['group']), str(group_result['group_winner']), streak)

        winner_index = rp_list.index(group_result['group_winner'])
        wins[winner_index] += 1
        winner_string = winner_string + str(winner_index)

        # Add a line break at byte boundries
        if bitwise_and(uint32(group_result['group']), uint32(255)) == 255:
            winner_string = winner_string + '\n'

        previous_result = group_result['group_winner']

    win_summary = ("max streak %r\n" %(max_streak))

    win_summary = win_summary + '\nTOTAL WINS\nrp\t\twins\n'

    for rp in rp_list:
        win_summary = win_summary + "{}\t{}".format(str(rp), wins[rp_list.index(rp)])


def save_results(results, rp_list, start_group, end_group, mask_length):

    # create a timestamp for use in filenames
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")

    # settings string to be copied at the beginning of each file
    settings_string = 'RPs: {}\nMask Length: {}\n Start Group: {}\n End Group: {}\n'.format(rp_list, mask_length, start_group, end_group)


    # save the RP and hash values to a file
    with open(timestamp + 'rp_hash_values.txt', 'w') as f:
        f.write(settings_string)
        f.write('group\t\t')
        for rp in rp_list:
            write(str(rp) + '\t')
        f.write('\n')

        for group_result in results:
            f.write(group_result['group'] + '\t')
            for result in group_result['group_results']:
                f.write(result['value'] + '\t')


    # save the winning RPs to a file
    with open(timestamp + 'winning_rps.txt', 'a'):
        f.write('group\twinner\tstreak')

    previous_result = ''
    streak = 1
    max_streak = 0
    winner_string = ''
    wins = [0] * len(rp_list)

    for group_result in results:

        if group_result['group_winner'] == previous_result:
            streak = streak + 1
        else:
            streak = 1
        if streak >= max_streak:
            max_streak = streak

        print("{}\t{}\t{}".format(str(group_result['group']), str(group_result['group_winner']), streak))

        winner_index = rp_list.index(group_result['group_winner'])
        wins[winner_index] += 1
        winner_string = winner_string + str(winner_index)

        # Add a line break at byte boundries
        if bitwise_and(uint32(group_result['group']), uint32(255)) == 255:
            winner_string = winner_string + '\n'

        previous_result = group_result['group_winner']

    print("max streak %r" %(max_streak))

    print('\nTOTAL WINS')

    print('rp\t\twins')
    for rp in rp_list:
        print("{}\t{}".format(str(rp), wins[rp_list.index(rp)]))

    print(winner_string)



if __name__ == '__main__':

    rp_list = []
    group_list = []

    mask_length = uint32(input('mask length: '))
    rp_input = input('rp addresses (separated by spaces): ')

    for rp in rp_input.split():

         rp = ipaddress.IPv4Address(rp)
         rp_list.append(rp)

    start_group = ipaddress.IPv4Address(input('starting group: '))
    end_group = ipaddress.IPv4Address(input('ending group: '))

    while start_group <= end_group:
        group_list.append(start_group)
        start_group+=1

    mask = uint32((2**mask_length) - 1 << 32-mask_length)


    with Pool(16) as pool:
        results = pool.map(partial(iter_rp, rp_list, mask), group_list)

