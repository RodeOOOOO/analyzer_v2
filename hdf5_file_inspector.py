import h5py

class HDF5FileInspector:
    def __init__(self, file_path):
        """
        Initialize the inspector with the HDF5 file path.
        """
        self.file_path = file_path

    def inspect_file(self):
        """
        Recursively inspect the HDF5 file structure to identify datasets and their shapes.
        """
        def inspect_group(group, path=""):
            dataset_info = []
            for key in group:
                item = group[key]
                full_path = f"{path}/{key}".strip("/")
                if isinstance(item, h5py.Dataset):
                    # Valid dataset
                    dataset_info.append((full_path, item.shape))
                    print(f"DEBUG: Dataset '{full_path}' has shape {item.shape}.")
                elif isinstance(item, h5py.Group):
                    # Nested group; recursively inspect
                    print(f"DEBUG: Found group '{full_path}', diving in...")
                    dataset_info.extend(inspect_group(item, full_path))
                else:
                    print(f"DEBUG: Unknown item type at '{full_path}'.")
            return dataset_info

        with h5py.File(self.file_path, "r") as f:
            print("DEBUG: Opened file successfully.")
            return inspect_group(f)

    def get_total_shape(self):
        """
        Get the total shape of all datasets combined as (rows, columns).
        """
        dataset_info = self.inspect_file()

        if not dataset_info:
            print("DEBUG: No valid datasets found.")
            return (0, 0)  # No datasets found

        total_rows = 0
        total_columns = 0

        for name, shape in dataset_info:
            if len(shape) == 2:  # Expecting 2D datasets
                total_rows = max(total_rows, shape[0])
                total_columns += shape[1]
            else:
                print(f"DEBUG: Dataset '{name}' has unexpected shape {shape}.")

        print(f"DEBUG: Calculated total shape as ({total_rows}, {total_columns}).")
        return (total_rows, total_columns)

    @staticmethod
    def test_main():
        """
        Test the HDF5FileInspector class using a hardcoded file path.
        """
        # Hardcoded file path
        file_path = "data/data.h5"

        # Initialize the inspector
        inspector = HDF5FileInspector(file_path)

        try:
            # Inspect datasets
            print(f"Inspecting HDF5 file: {file_path}")
            dataset_info = inspector.inspect_file()

            # Print dataset headers and value counts
            print("Dataset Headers and Shapes:")
            for name, shape in dataset_info:
                print(f"  {name}: {shape}")

            # Print total shape
            total_shape = inspector.get_total_shape()
            print(f"Total Shape of Data: {total_shape}")
        except Exception as e:
            print(f"An error occurred: {e}")

def main():
    """
    Main function to run the HDF5FileInspector.
    """
    HDF5FileInspector.test_main()

if __name__ == "__main__":
    main()
