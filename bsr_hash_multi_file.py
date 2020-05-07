import ipaddress

from datetime import datetime
from numpy import uint32, bitwise_and, bitwise_xor

from functools import partial
from multiprocessing import Pool
from warnings import filterwarnings

def calculate_hash(rp_address, group, mask):

    """
        implements the hash function from RFC 7761
    """

    # supress overflow warnings. These are expected with 32bit arithmetic 
    filterwarnings('ignore', category=RuntimeWarning)

    result = uint32(bitwise_and(group,mask))
    result = uint32(uint32(1103515245) * uint32(result)) + uint32(12345)
    result = uint32(bitwise_xor(result, rp_address))
    result = uint32(uint32(1103515245) * uint32(result))
    result = uint32(uint32(result) + uint32(12345))
    result = uint32(uint32(result) % uint32(2**31))

    return result


def iter_rp(rp_list, mask, group):

    """
        iterates over the RP list, calls calculate_hash and stores the results
    """

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


def calculate_winners(results, rp_list):

    # values used to calculate streak lengths
    previous_result = ''
    streak = 1
    max_streak = 0
    
    # stores win counts
    wins = [0] * len(rp_list)

    # stores a list of winning RP numbers in order from lowest group number to highest
    win_string = ''

    # stores the overall results
    result_string = ''

    for group_result in results:

        # calculate streak length
        if group_result['group_winner'] == previous_result:
            streak = streak + 1
        else:
            streak = 1
        if streak >= max_streak:
            max_streak = streak

        # build the result string for the current group
        result_string = result_string + "{}\t{}\t{}\n".format(str(group_result['group']), str(group_result['group_winner']), streak)

        # increment the wins count and build the win_string
        winner_index = rp_list.index(group_result['group_winner'])
        wins[winner_index] += 1
        win_string = win_string + str(winner_index)

        # Add a line break to the win_string at byte boundries
        # this allows us to build a winning RP map
        if bitwise_and(uint32(group_result['group']), uint32(255)) == 255:
            win_string = win_string + '\n'

        # set the prior result to current result
        previous_result = group_result['group_winner']


    # build win_summary
    win_summary = ("max streak %r\n" %(max_streak))
    win_summary = win_summary + '\nTOTAL WINS\nrp\t\t\twins\n'

    for rp in rp_list:
        win_summary = win_summary + "{}\t{}\n".format(str(rp), wins[rp_list.index(rp)])

    return result_string, win_summary, win_string


def save_results(results, rp_list, start_group, end_group, mask_length):

    # create a timestamp for use in filenames
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")

    # settings string to be copied at the beginning of each file
    settings_string = 'RPs: '
    for rp in rp_list:
        settings_string = settings_string + '{} '.format(str(rp))

    settings_string = settings_string + '\nMask Length: {}\n Start Group: {}\n End Group: {}\n'.format(mask_length, start_group, end_group)

    win_results, win_summary, win_string = calculate_winners(results, rp_list)

    # save the win_string to a file
    with open(timestamp + '_win_map.txt', 'a') as f:
        f.write(settings_string)
        f.write(win_summary)
        f.write(win_string)

    save_rp_wins = input('save RP Win list to file? [n]/y :').lower()

    if('y' in save_rp_wins):
        # save the winning RPs to a file
        with open(timestamp + '_winning_rps.txt', 'a') as f:
            f.write(settings_string)
            f.write(win_summary)
            f.write('group\t\twinner\tstreak\n')
            f.write(win_results)

    save_hash_values = input('save hash values to file? [n]/y :').lower()

    if('y' in save_hash_values):
        # save hash values to a file
        with open(timestamp + '_rp_hash_values.txt', 'w') as f:

            f.write(settings_string)
            f.write('group\t\t')
            for rp in rp_list:
                f.write(str(rp) + '\t')
            f.write('\n')

            # store the results in a buffer first and then write to the file
            group_result_buffer = ''

            for group_result in results:
                group_result_buffer = group_result_buffer + str(group_result['group']) + '\t'
                for result in group_result['group_results']:
                    group_result_buffer = group_result_buffer + str(result['value']) + '\t'
                group_result_buffer = group_result_buffer + '\n'

            f.write(group_result_buffer)



if __name__ == '__main__':

    rp_list = []
    group_list = []

    # prompt for user inpt
    mask_length = uint32(input('mask length: '))
    rp_input = input('rp addresses (separated by spaces): ')
    start_group = ipaddress.IPv4Address(input('starting group: '))
    end_group = ipaddress.IPv4Address(input('ending group: '))

    # build the rp_list based on user input
    for rp in rp_input.split():

         rp = ipaddress.IPv4Address(rp)
         rp_list.append(rp)

    # build a list of groups, required for using Pool.map()
    curr_group = start_group
    
    while curr_group <= end_group:
        group_list.append(curr_group)
        curr_group+=1

    # convert the mask_length to an actual bitmask of the appropriate length
    mask = uint32((2**mask_length) - 1 << 32-mask_length)

    # spawn 16 processes to calculate results
    with Pool(16) as pool:
        results = pool.map(partial(iter_rp, rp_list, mask), group_list)

    # save the results to a file
    save_results(results, rp_list, start_group, end_group, mask_length)