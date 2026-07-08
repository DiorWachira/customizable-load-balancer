import math

class ConsistentHashMap:
    def __init__(self, num_slots=512):
        self.num_slots = num_slots
        # The ring is represented as an array of size 512, initialized to None
        self.ring = [None] * self.num_slots
        # Track active physical server hostnames to maintain their positions easily
        self.physical_servers = set()

    def _hash_request(self, i: int) -> int:
        """Hash function for request mapping: H(i) = i + 2i^2 + 17"""
        return (i + 2 * (i ** 2) + 17) % self.num_slots

    def _hash_virtual_server(self, i: int, j: int) -> int:
        """Hash function for virtual server mapping: Phi(i, j) = i + j + 2j^2 + 25"""
        return (i + j + 2 * (j ** 2) + 25) % self.num_slots

    def _extract_server_id(self, hostname: str) -> int:
        """
        Extracts a numeric ID from a hostname string (e.g., 'Server 1' -> 1, 'S5' -> 5).
        If no numbers are present, it falls back to a hash fallback to prevent crashes.
        """
        digits = ''.join(filter(str.isdigit, hostname))
        if digits:
            return int(digits)
        return sum(ord(c) for c in hostname)

    def add_server(self, hostname: str):
        """Adds a physical server and its 9 virtual instances to the ring."""
        if hostname in self.physical_servers:
            return
        
        self.physical_servers.add(hostname)
        server_id = self._extract_server_id(hostname)
        num_virtual_servers = int(math.log2(self.num_slots))  # log2(512) = 9

        for j in range(1, num_virtual_servers + 1):
            slot = self._hash_virtual_server(server_id, j)
            
            # Linear Probing: handle conflict if two virtual servers hit the same slot
            while self.ring[slot] is not None:
                slot = (slot + 1) % self.num_slots
                
            self.ring[slot] = hostname

    def remove_server(self, hostname: str):
        """Removes a physical server and all its virtual instances from the ring."""
        if hostname not in self.physical_servers:
            return
        
        self.physical_servers.remove(hostname)
        # Clear all slots containing this specific hostname
        for slot in range(self.num_slots):
            if self.ring[slot] == hostname:
                self.ring[slot] = None

    def get_server(self, request_id: int) -> str:
        """Maps a 6-digit request ID to the nearest clockwise server container."""
        if not self.physical_servers:
            return None

        # Compute starting slot for the request
        start_slot = self._hash_request(request_id)
        slot = start_slot

        # Clockwise traversal to find the nearest non-empty server slot
        while True:
            if self.ring[slot] is not None:
                return self.ring[slot]
            slot = (slot + 1) % self.num_slots
            
            # Guard against infinite loops if the map somehow emptied unexpectedly
            if slot == start_slot:
                break
                
        return None
