import tkinter as tk
import tkinter.messagebox as msgbox
import time
from itertools import product, permutations
from collections import namedtuple
from random import randint

GridCoords = namedtuple('GridCoords', 'row column')

# A játék osztályának definíciója, amely egyben a GUI főablaka is.
class SlidingPuzzle(tk.Tk):
    def __init__(self, board_rows: int = 4, board_columns: int = 4):
        super().__init__()
        self.board_rows, self.board_columns = board_rows, board_columns

        # A főablak címe, mérete, pozíciója, színe és szegélyformája.
        self.title(f'TILI-TOLI {self.board_rows}x{self.board_columns}')
        self.root_width, self.root_height = board_columns * 100, board_rows * 100
        scr_w, scr_h = self.winfo_screenwidth(), self.winfo_screenheight()
        root_x, root_y = scr_w // 2 - self.root_width // 2, scr_h // 2 - self.root_height // 2
        self.geometry('{}x{}+{}+{}'.format(self.root_width, self.root_height, root_x, root_y))
        self.config(bg='gray50', relief=tk.RIDGE, bd=10)
        self.resizable(False, False)

        # A játéktér mezőkkel való feltöltése a megoldást jelentő elrendezésben, az üres mező grid-koordinátáinak
        # feljegyzése, és utána a mezők megkeverése.
        self.populate_with_fields()
        self.empty_field = GridCoords(board_rows - 1, board_columns - 1)
        self.shuffle_fields()

        # A mezőmozgatás-számláló kezdőérték beállítás, és játékidő mérés indítása.
        self.moves = 0
        self.start = time.perf_counter()

    def populate_with_fields(self):
        """A mezőket megjelenítő grafikus elemek (számozott keretek) lehelyezése a játéktérre a megoldást
        jelentő elrendezésben A jobb alsó mező üres marad.
        """
        for ri, ci in product(range(self.board_rows), range(self.board_columns)):
            # Mindaddig lehelyezünk kereteket, amíg a jobb alsó cellát el nem érjük.
            if not ((ri, ci) == (self.board_rows - 1, self.board_columns - 1)):
                # A mezőket képviselő keretek méretének meghatározása, igazodva a játéktábla méretéhez.
                frm_width = (self.root_width - 2 * int(self.cget('bd'))) / self.board_columns
                frm_height = (self.root_height - 2 * int(self.cget('bd'))) / self.board_rows
                # A mezőket megjelenítő keretek létrehozása és kivitelük konfigurálása.
                frm = tk.Frame(self, bg='white', width=frm_width, height=frm_height, relief=tk.RIDGE)
                # A mezőket képviselő keretek táblázatos lehelyezése.
                frm.grid(row=ri, column=ci)
                frm.pack_propagate(False)

                # A mezőkeretekre egy-egy címkét helyezünk, amelyek egyesével növekvő számokat jelenítenek meg.
                nums = ri * self.board_columns + ci + 1
                lbl = tk.Label(frm, text=str(nums))
                # A címkék számfeliratának betűméretét a játéktér méretéhez és a sorok/oszlopok számához igazítjuk.
                # Viszonyítási alapnak egy 4 sorból és 4 oszlopból álló, 400x400 képpont méretű táblát
                # veszünk, amelyen a betűméret 34.
                font_size = int(34 * (4 / max(self.board_rows, self.board_columns)) * (
                        max(self.root_width, self.root_height) / 400))
                # A címkék színeit úgy állítjuk be, hogy váltakozva eltérők legyenek.
                bg_color = 'white'
                if (ri % 2 == 0 and ci % 2 != 0) or (ri % 2 != 0 and ci % 2 == 0):
                    bg_color = 'maroon'
                # A címke betűtípusának, színjellemzőinek és kivitelének beállítása.
                lbl.config(bg=bg_color, fg='goldenrod', font=('Consolas', font_size, 'bold'),
                           relief=tk.RAISED, bd=5)
                # A címke lehelyezése a keretben.
                lbl.pack(fill=tk.BOTH, expand=True)
                # Eseménykezelő (bal egérgomb kattintás) hozzárendelése a címkéhez.
                lbl.bind('<Button 1>', self.move_field)

    def find_neighbors_of(self, grid_coords: GridCoords) -> set[GridCoords]:
        """A megadott grid-koordinátájú mező szomszédjainak koordinátáit adja vissza.
        A szomszédok azok, amelyek koordinátái eggyel nagyobbak vagy eggyel kisebbek az adott mezőjénél, de
        nem kisebbek mint 0 és nem nagyobbak a maximális sor- és oszlopindexeknél."""
        neighbor_offsets = [GridCoords(*offset) for offset in permutations([-1, 0, 1], 2) if 0 in offset]
        potental_neighbors = {GridCoords(grid_coords.row + offset.row, grid_coords.column + offset.column)
                              for offset in neighbor_offsets}
        neighbors = {GridCoords(x, y) for x, y in potental_neighbors if
                     -1 < x < self.board_rows and -1 < y < self.board_columns}
        return neighbors

    def shuffle_fields(self):
        """A mezők keverése. A keverés nem lehet teljesen tetszőleges, mert akkor lehet, hogy nem lesz megoldás.
        Ezért a keverés úgy történik, hogy a megoldást jelentő elrendezésből kiindulva az üres mező szomszédai közül
        választunk egyet véletlenszerűen, és azt mozgatjuk az üres mező helyére, és ezt ismételjük egy adott számszor.
        """
        for _ in range(500):
            # Meghatározzuk az üres mező szomszédait.
            neighbors: list[GridCoords] = list(self.find_neighbors_of(self.empty_field))
            # A szomszédok közül véletlenszerűen kiválasztunk egyet, amit az üres cella helyére mozgatunk.
            random_index = randint(0, len(neighbors) - 1)
            selected_field_coords = neighbors[random_index]
            # Megkeressük a kiválasztott grid-koordinátákhoz tartozó keret elemet.
            selected_frm = self.grid_slaves(selected_field_coords.row, selected_field_coords.column)[0]
            # Ezt a keretet az eddig üres mező helyére helyezzük, az üres mezőhöz pedig a keret korábbi
            # koordinátáit rendeljük.
            selected_frm.grid(row=self.empty_field.row, column=self.empty_field.column)
            self.empty_field = selected_field_coords

    def move_field(self, event):
        """Az eseménnyel érintett mező áthelyezése. Ennek során a lépésszámlálőt is növeljük és az áthelyezés után
        ellőrizzük, hogy a megoldást jelentő elrendezést kaptuk-e.
        """
        self.moves += 1
        self.change_field_position(event)
        self.check_if_solved()

    def change_field_position(self, event):
        """Az eseménnyel érintett mező áthelyezése, azaz új grid-koordinátáinak meghatározása és ide történő áthelyzése.
        """
        # Meghatározzuk az üres mező szomszédait.
        neighbors = self.find_neighbors_of(self.empty_field)
        # Meghatározzuk a kiválasztott mezőt reprezentáló keret-elem grid-koordinátáit.
        frm = event.widget.master
        gridinfo = frm.grid_info()
        selected_field_coords = GridCoords(gridinfo['row'], gridinfo['column'])

        # Ha az üres mező szomszédai között van a játékos által kiválasztott mező, akkor azt az üres mezőre helyezzük.
        # Az üres mező grid-koordinátáit a kiválasztott mező korábbi koordinátáira állítjuk be.
        # Ha a kiválasztott mező nincs a szomszédok között, akkor nem történik semmi.
        if selected_field_coords in neighbors:
            frm.grid(row=self.empty_field.row, column=self.empty_field.column)
            self.empty_field = selected_field_coords

    def check_if_solved(self):
        # Ellenőrizzük, hogy megoldott-e a játék, vagyis a mezők, illetve az azokon levő számok a megoldást jelentő
        # elrendezésben vannak-e a játéktéren.
        for ri, ci in product(range(self.board_rows), range(self.board_columns)):
            # Kinyerjük a játéktér adott grid-koordinátáján levő grafikus elemet.
            widget_list: list = self.grid_slaves(ri, ci)
            if widget_list:
                # Ha nem üres a lista, azaz nem üres mezőről van szó, akkor a megtalál kereten levő címke számot jelentő
                # szövegét kikérjük és ellenőrizzük, hogy a szám a megoldást jelentő elrendezésnek megfelelő-e.
                # Ha nem, akkor kilépünk az ellenőrzésből.
                if not widget_list[0].slaves()[0].cget("text") == str(ri * self.board_columns + ci + 1):
                    return
        # Ha minden mezőn levő szám megfelel a megoldási elrendezés szerintinek, akkor leállítjuk az időmérést,
        # meghatározzuk a játékidőt, majd a megoldáshoz vezető lépésszámmal együtt egy, a sikeres megoldásról
        # tájékoztató üzenetablakban ezeket kiírjuk, és végül rákérdezünk, hogy akar-e új játékot kezdeni.
        stop = time.perf_counter()
        duration = stop - self.start
        minute, second = divmod(int(duration), 60)

        response = msgbox.askyesno(self.title(), f'SIKERES MEGOLDÁS!',
                                   detail=f'Lépések száma: {self.moves}\n'
                                          f'Megoldási idő: {minute} perc {second} másodperc\n\n'
                                          f'Akarsz új játékot kezdeni?',
                                   icon=msgbox.INFO)
        # Ha új játok szeretne a játékos, akkor folytatjuk a mezők megkeverésével. Ha pedig nem, akkor
        # kilépünk a programból.
        if response is True:
            self.shuffle_fields()
        else:
            self.destroy()

    def run(self):
        self.mainloop()


if __name__ == '__main__':
    # Adott sorból és oszlopból álló játék létrehozása és a játék indítása.
    game = SlidingPuzzle(4, 4)
    game.run()
