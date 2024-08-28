using UnityEngine;

public class KeyboardMovement : MonoBehaviour
{
    public float moveSpeed = 5f;
    public float lookSpeed = 2f;

    private CharacterController characterController;
    private Camera playerCamera;
    private float verticalRotation = 0f;

    void Start()
    {
        characterController = GetComponent<CharacterController>();
        playerCamera = Camera.main; // Ensure your camera is tagged as "MainCamera"
    }

    void Update()
    {
        if (Input.GetKey(KeyCode.W))
            MoveForward();
        if (Input.GetKey(KeyCode.S))
            MoveBackward();
        if (Input.GetKey(KeyCode.A))
            MoveLeft();
        if (Input.GetKey(KeyCode.D))
            MoveRight();

        if (Input.GetKey(KeyCode.LeftShift))
            moveSpeed = 10f; // Adjust speed for sprinting
        else
            moveSpeed = 5f;

        if (characterController != null && playerCamera != null)
        {
            float h = Input.GetAxis("Mouse X") * lookSpeed;
            float v = Input.GetAxis("Mouse Y") * lookSpeed;
            
            verticalRotation -= v;
            verticalRotation = Mathf.Clamp(verticalRotation, -90f, 90f);
            
            playerCamera.transform.localRotation = Quaternion.Euler(verticalRotation, 0f, 0f);
            transform.Rotate(Vector3.up * h);
        }
    }

    void MoveForward()
    {
        Vector3 move = transform.forward * moveSpeed * Time.deltaTime;
        characterController.Move(move);
    }

    void MoveBackward()
    {
        Vector3 move = -transform.forward * moveSpeed * Time.deltaTime;
        characterController.Move(move);
    }

    void MoveLeft()
    {
        Vector3 move = -transform.right * moveSpeed * Time.deltaTime;
        characterController.Move(move);
    }

    void MoveRight()
    {
        Vector3 move = transform.right * moveSpeed * Time.deltaTime;
        characterController.Move(move);
    }
}
